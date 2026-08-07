"""Dataset import (T-11's import half, PLAN §4.1 Data Collection Plan row):
CSV (stdlib csv) or XLSX (openpyxl, pinned) upload -> column-type inference
(user-confirmable before save) -> an import quality scan (missing values,
non-numeric values in numeric columns, duplicate rows, row count --
rubric R-MEA-06's "basic data-quality checks are visibly done"). Saved
under the project folder as datasets/<id>/v1.csv (one canonical CSV
regardless of source format) + meta.json (SHA-256 of that exact file,
confirmed column types, source filename, the quality scan). The SHA-256
is the provenance anchor routes/stats.py's dataset-sourced /stats/baseline
echoes back alongside its BaselineResult, so a reviewer can independently
re-hash v1.csv and confirm it matches what a given baseline was computed
from (R-MEA-06: "provenance hash links dataset -> any BaselineResult").

No multipart upload: this milestone's pinned-dependency list is openpyxl
only (build brief hard rule), and FastAPI's UploadFile support needs
python-multipart, which isn't installed and isn't on the allowed-new-deps
list. Files travel as base64 inside an ordinary JSON body instead --
consistent with every other route in this engine (routes/*.py is all-JSON
already; multipart would have been the one odd endpoint out).
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import io
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Literal

import openpyxl
from pydantic import BaseModel

from .project_store import ProjectStore

ColumnType = Literal["numeric", "text"]

SAMPLE_VALUES_PER_COLUMN = 5
PREVIEW_SAMPLE_ROWS = 10


class ColumnInfo(BaseModel):
    name: str
    inferred_type: ColumnType
    # Effective type: a caller's confirmed override if one was given for
    # this column, else inferred_type -- what build_columns()'s docstring
    # calls "inferred but user-confirmable."
    type: ColumnType
    sample_values: list[str]


class QualityScanResult(BaseModel):
    row_count: int
    missing_values: dict[str, int]
    non_numeric_in_numeric_columns: dict[str, int]
    duplicate_row_count: int


class DatasetPreview(BaseModel):
    """Returned by the preview route -- never persisted. Replayable: the
    same upload can be previewed again and again as the user tries
    different column-type overrides, right up until they hit save."""

    source_filename: str
    row_count: int
    columns: list[ColumnInfo]
    quality: QualityScanResult
    sample_rows: list[dict[str, str]]


class DatasetMeta(BaseModel):
    """The persisted record (meta.json) -- plain and mutable-by-convention
    like project_store.py's ProjectMetadata, not frozen like stats/*.py's
    Computed[T] results: this is a stored data record, not a scientific
    computation whose immutability the schema itself should enforce."""

    schema_version: int = 1
    dataset_id: str
    project_id: str
    source_filename: str
    created_at: str
    sha256: str
    row_count: int
    columns: list[ColumnInfo]
    quality: QualityScanResult


# --- Parsing: CSV (stdlib) / XLSX (openpyxl) -> one common (header, rows) shape ---


def _parse_csv_bytes(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    # utf-8-sig strips a BOM if present (common from Excel "CSV UTF-8" exports).
    text = content.decode("utf-8-sig")
    raw_rows = [r for r in csv.reader(io.StringIO(text)) if r]  # drop fully-blank lines
    if not raw_rows:
        raise ValueError("the file has no rows")
    header = [h.strip() for h in raw_rows[0]]
    if not any(header):
        raise ValueError("the file has no column headers")
    rows: list[dict[str, str]] = []
    for r in raw_rows[1:]:
        rows.append({header[i]: (r[i].strip() if i < len(r) else "") for i in range(len(header))})
    return header, rows


def _xlsx_cell_to_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return str(value).strip()


def _parse_xlsx_bytes(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        rows_iter = workbook.worksheets[0].iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            raise ValueError("the file has no rows") from None
        header = [_xlsx_cell_to_str(h) for h in header_row]
        if not any(header):
            raise ValueError("the file has no column headers")
        rows: list[dict[str, str]] = []
        for r in rows_iter:
            values = [_xlsx_cell_to_str(v) for v in r]
            if not any(v != "" for v in values):
                continue  # trailing/blank row -- not real data
            rows.append({header[i]: (values[i] if i < len(values) else "") for i in range(len(header))})
        return header, rows
    finally:
        workbook.close()


def parse_upload(content: bytes, source_filename: str) -> tuple[list[str], list[dict[str, str]]]:
    suffix = Path(source_filename).suffix.lower()
    if suffix == ".csv":
        return _parse_csv_bytes(content)
    if suffix == ".xlsx":
        return _parse_xlsx_bytes(content)
    raise ValueError(f"unsupported file type {suffix!r} -- only .csv and .xlsx are supported")


# --- Column-type inference (user-confirmable) + the import quality scan ---


def infer_column_type(values: list[str]) -> ColumnType:
    non_empty = [v for v in values if v.strip() != ""]
    if not non_empty:
        return "text"  # nothing to judge -- default to text rather than guess
    for v in non_empty:
        try:
            float(v)
        except ValueError:
            return "text"
    return "numeric"


def build_columns(header: list[str], rows: list[dict[str, str]], type_overrides: dict[str, str] | None) -> list[ColumnInfo]:
    overrides = type_overrides or {}
    columns: list[ColumnInfo] = []
    for name in header:
        values = [row.get(name, "") for row in rows]
        inferred = infer_column_type(values)
        override = overrides.get(name)
        effective: ColumnType = override if override in ("numeric", "text") else inferred  # type: ignore[assignment]
        samples = [v for v in values if v.strip() != ""][:SAMPLE_VALUES_PER_COLUMN]
        columns.append(ColumnInfo(name=name, inferred_type=inferred, type=effective, sample_values=samples))
    return columns


def scan_quality(columns: list[ColumnInfo], rows: list[dict[str, str]]) -> QualityScanResult:
    """R-MEA-06's "basic data-quality checks visibly done": missing cells,
    non-numeric cells in a column typed numeric, and exact-duplicate rows
    -- run against whatever types are effective *right now* (inferred, or
    a caller's override), so a preview re-scans live as the user fixes a
    column's type before ever saving anything."""
    missing = {c.name: 0 for c in columns}
    non_numeric = {c.name: 0 for c in columns}
    seen: set[tuple[str, ...]] = set()
    duplicate_row_count = 0
    for row in rows:
        key = tuple(row.get(c.name, "") for c in columns)
        if key in seen:
            duplicate_row_count += 1
        else:
            seen.add(key)
        for c in columns:
            val = row.get(c.name, "")
            if val.strip() == "":
                missing[c.name] += 1
            elif c.type == "numeric":
                try:
                    float(val)
                except ValueError:
                    non_numeric[c.name] += 1
    return QualityScanResult(
        row_count=len(rows), missing_values=missing,
        non_numeric_in_numeric_columns=non_numeric, duplicate_row_count=duplicate_row_count,
    )


def build_preview(content: bytes, source_filename: str, type_overrides: dict[str, str] | None) -> DatasetPreview:
    header, rows = parse_upload(content, source_filename)
    columns = build_columns(header, rows, type_overrides)
    quality = scan_quality(columns, rows)
    return DatasetPreview(
        source_filename=source_filename, row_count=len(rows), columns=columns,
        quality=quality, sample_rows=rows[:PREVIEW_SAMPLE_ROWS],
    )


# --- Normalized storage: v1.csv (canonical CSV, any source format) + meta.json ---


def _rows_to_csv_bytes(header: list[str], rows: list[dict[str, str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header)
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in header})
    return buf.getvalue().encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    # Same temp-file+rename technique as project_store.py's
    # _atomic_write_json, generalized to bytes so v1.csv and meta.json
    # both get it -- a crash mid-write never leaves a half-written file.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _not_float(value: str) -> bool:
    try:
        float(value)
        return False
    except ValueError:
        return True


class DatasetStore:
    """Sibling of ProjectStore, not a stats/*.py module: DatasetMeta and
    friends stay plain (unfrozen) records -- see DatasetMeta's docstring."""

    def __init__(self, project_store: ProjectStore) -> None:
        self.projects = project_store

    def _dataset_dir(self, project_id: str, dataset_id: str) -> Path:
        return self.projects.resolved_project_path(project_id) / "datasets" / dataset_id

    def save_dataset(
        self, project_id: str, source_filename: str, content: bytes,
        type_overrides: dict[str, str] | None, created_at: str,
    ) -> DatasetMeta:
        self.projects.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
        header, rows = parse_upload(content, source_filename)
        columns = build_columns(header, rows, type_overrides)
        quality = scan_quality(columns, rows)
        csv_bytes = _rows_to_csv_bytes(header, rows)
        meta = DatasetMeta(
            dataset_id=uuid.uuid4().hex, project_id=project_id, source_filename=source_filename,
            created_at=created_at, sha256=hashlib.sha256(csv_bytes).hexdigest(),
            row_count=len(rows), columns=columns, quality=quality,
        )
        d = self._dataset_dir(project_id, meta.dataset_id)
        _atomic_write(d / "v1.csv", csv_bytes)
        _atomic_write(d / "meta.json", json.dumps(meta.model_dump(mode="json"), indent=2, sort_keys=True).encode("utf-8"))
        return meta

    def list_datasets(self, project_id: str) -> list[DatasetMeta]:
        base = self.projects.resolved_project_path(project_id) / "datasets"
        if not base.exists():
            return []
        metas = [self.load_meta(project_id, p.name) for p in sorted(base.iterdir()) if (p / "meta.json").exists()]
        return sorted(metas, key=lambda m: m.created_at)

    def load_meta(self, project_id: str, dataset_id: str) -> DatasetMeta:
        path = self._dataset_dir(project_id, dataset_id) / "meta.json"
        if not path.exists():
            raise FileNotFoundError(f"dataset {dataset_id!r} not found in project {project_id!r}")
        return DatasetMeta.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def load_rows(self, project_id: str, dataset_id: str) -> list[dict[str, str]]:
        meta = self.load_meta(project_id, dataset_id)
        text = (self._dataset_dir(project_id, dataset_id) / "v1.csv").read_text(encoding="utf-8")
        names = [c.name for c in meta.columns]
        return [{name: (row.get(name) or "") for name in names} for row in csv.DictReader(io.StringIO(text))]

    def load_numeric_column(self, project_id: str, dataset_id: str, column: str) -> tuple[list[float], DatasetMeta]:
        meta = self.load_meta(project_id, dataset_id)
        col = next((c for c in meta.columns if c.name == column), None)
        if col is None:
            raise KeyError(f"column {column!r} not found in dataset {dataset_id!r}")
        if col.type != "numeric":
            raise ValueError(f"column {column!r} is not numeric (type={col.type!r}) -- baseline requires a numeric column")
        raw = [row.get(column, "") for row in self.load_rows(project_id, dataset_id)]
        bad_count = sum(1 for v in raw if v.strip() == "" or _not_float(v))
        if bad_count:
            raise ValueError(
                f"column {column!r} has {bad_count} missing/non-numeric value(s) -- the import quality scan "
                "flagged this; clean the data or pick a different column rather than silently dropping rows"
            )
        return [float(v) for v in raw], meta
