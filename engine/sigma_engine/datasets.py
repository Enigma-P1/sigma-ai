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

Once saved, a dataset was read-only forever -- no way to fix a row without
re-exporting from a spreadsheet and re-uploading. Two uncertified-supervisor
UAT testers hit that wall on real data (docs/uat/README.md, PLAN.md Phase 1):
one tester's Pareto counted "JM" and "J Morales" as two separate members of
the vital few -- the same man, two spellings -- with no way to merge them.
derive_dataset (below) is the fix, and it is deliberately NOT an in-place
edit: it always produces a second, independent dataset (new dataset_id, new
v1.csv, new sha256), because sha256 is the provenance anchor routes/
stats.py's dataset-sourced /stats/baseline echoes back beside a
BaselineResult (R-MEA-06) -- a chart computed last week has to keep
resolving to the exact bytes it was computed from, and mutating v1.csv in
place would silently break that anchor for every result already computed
against the parent. A new dataset cannot.
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
from typing import Annotated, Literal

import openpyxl
from pydantic import BaseModel, Field

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


# --- Derivations: a saved dataset -> a NEW dataset, one of four kinds ---
#
# See this module's docstring for why a derivation can never just rewrite
# v1.csv in place. `kind` tags which of the four shapes below a given
# Derivation is (a Pydantic discriminated union -- FastAPI 422s
# automatically on an unrecognized kind or a variant missing its own
# required fields, same as every other request model in this engine).
# meta.json stores whichever variant was used verbatim, so -- recode above
# all -- the exact mapping that changed the data stays a permanent,
# exportable part of the record instead of vanishing into an edited cell:
# this app's stated position is "the scan finds problems, it never
# silently fixes them."


class CellEdit(BaseModel):
    row_index: int
    column: str
    value: str


class EditCellsDerivation(BaseModel):
    kind: Literal["edit_cells"] = "edit_cells"
    edits: list[CellEdit] = Field(min_length=1)


class AddRowDerivation(BaseModel):
    kind: Literal["add_row"] = "add_row"
    # Keyed by column name; any column this dict leaves out becomes "" in
    # the new row -- the same "a short row pads with blanks" rule
    # _parse_csv_bytes/_parse_xlsx_bytes already apply to an ordinary
    # upload, not a stricter one invented just because this row arrived
    # one field at a time instead of inside a file.
    values: dict[str, str] = Field(default_factory=dict)


class DeleteRowsDerivation(BaseModel):
    kind: Literal["delete_rows"] = "delete_rows"
    row_indices: list[int] = Field(min_length=1)


class RecodeDerivation(BaseModel):
    kind: Literal["recode"] = "recode"
    column: str
    # source value -> target value, e.g. {"JM": "J. Morales", "J Morales":
    # "J. Morales"} -- multiple keys are free to point at the same target
    # (that IS the vital-few fix). A plain dict rather than {targets: [...],
    # sources: [...]} because this mapping is meant to be read straight out
    # of meta.json, not reconstructed from some other derived view of it.
    mapping: dict[str, str] = Field(min_length=1)


class DeriveColumnDerivation(BaseModel):
    kind: Literal["derive_column"] = "derive_column"
    new_column_name: str = Field(min_length=1)
    left_column: str
    right_column: str
    # "group by Item ordered AND Item shipped" needs one category column
    # a Pareto can group on; joining two existing ones with a visible
    # separator is that column, without teaching the rest of this engine's
    # stats/*.py a second grouping axis it doesn't otherwise have.
    separator: str = " → "


Derivation = Annotated[
    EditCellsDerivation | AddRowDerivation | DeleteRowsDerivation | RecodeDerivation | DeriveColumnDerivation,
    Field(discriminator="kind"),
]


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
    # Provenance the other direction (T-08/T-09's zero-re-entry contract,
    # rubric R-MEA-06 #3): which in-app artifact this dataset was
    # materialized from, if any. None for an ordinary CSV/XLSX upload --
    # only a tool's own to_dataset action sets these (routes/check_sheet.py,
    # routes/time_study.py). Optional with a default so every dataset saved
    # before this field existed still loads unchanged.
    source_artifact_id: str | None = None
    source_tool_id: str | None = None

    # Derivation lineage (module docstring). Both optional with a default,
    # same "every dataset saved before this field existed still loads
    # unchanged" contract as source_artifact_id/source_tool_id above --
    # None for an ordinary upload; only DatasetStore.derive_dataset sets
    # these, on the dataset it just created.
    derived_from_dataset_id: str | None = None
    derivation: Derivation | None = None
    # The other direction: set on the PARENT the moment a child is derived
    # from it, so a UI can default to showing the newest of a lineage
    # without deleting or hiding the history a superseded dataset still is.
    superseded_by_dataset_id: str | None = None


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


# --- Derivations: kind-specific (header, rows) transforms ---
#
# Each function takes the PARENT's (header, rows) and one concrete
# Derivation and returns a NEW (header, rows) -- the parent's own lists and
# dicts are never mutated in place, since DatasetStore.derive_dataset still
# needs the parent's original rows intact to write the child from and to
# leave the parent's v1.csv untouched afterward. All raise ValueError on an
# invalid derivation (out-of-range index, unknown column, ...); the route
# layer turns that into a 422, same convention as parse_upload/save_dataset.


def _check_row_index(index: int, row_count: int) -> None:
    if not (0 <= index < row_count):
        raise ValueError(f"row_index {index} is out of range for a dataset with {row_count} row(s)")


def _check_column(name: str, header: list[str]) -> None:
    if name not in header:
        raise ValueError(f"column {name!r} not found -- this dataset's columns are {header}")


def _apply_edit_cells(header: list[str], rows: list[dict[str, str]], d: EditCellsDerivation) -> tuple[list[str], list[dict[str, str]]]:
    new_rows = [dict(row) for row in rows]
    for edit in d.edits:
        _check_row_index(edit.row_index, len(rows))
        _check_column(edit.column, header)
        new_rows[edit.row_index][edit.column] = edit.value
    return header, new_rows


def _apply_add_row(header: list[str], rows: list[dict[str, str]], d: AddRowDerivation) -> tuple[list[str], list[dict[str, str]]]:
    for name in d.values:
        _check_column(name, header)
    new_row = {name: d.values.get(name, "") for name in header}
    return header, [*rows, new_row]


def _apply_delete_rows(header: list[str], rows: list[dict[str, str]], d: DeleteRowsDerivation) -> tuple[list[str], list[dict[str, str]]]:
    for index in d.row_indices:
        _check_row_index(index, len(rows))
    drop = set(d.row_indices)
    new_rows = [row for i, row in enumerate(rows) if i not in drop]
    return header, new_rows


def _apply_recode(header: list[str], rows: list[dict[str, str]], d: RecodeDerivation) -> tuple[list[str], list[dict[str, str]]]:
    _check_column(d.column, header)
    for source, target in d.mapping.items():
        if target.strip() == "":
            raise ValueError(
                f"recode target for {source!r} would be empty -- recode consolidates spellings into one visible "
                "value, it doesn't blank cells; use edit_cells (or delete_rows) if blanking/removing is really the intent"
            )
    new_rows = []
    for row in rows:
        new_row = dict(row)
        current = new_row.get(d.column, "")
        if current in d.mapping:
            new_row[d.column] = d.mapping[current]
        new_rows.append(new_row)
    return header, new_rows


def _apply_derive_column(header: list[str], rows: list[dict[str, str]], d: DeriveColumnDerivation) -> tuple[list[str], list[dict[str, str]]]:
    _check_column(d.left_column, header)
    _check_column(d.right_column, header)
    if d.new_column_name in header:
        raise ValueError(f"column {d.new_column_name!r} already exists in this dataset")
    new_header = [*header, d.new_column_name]
    new_rows = []
    for row in rows:
        new_row = dict(row)
        new_row[d.new_column_name] = f"{row.get(d.left_column, '')}{d.separator}{row.get(d.right_column, '')}"
        new_rows.append(new_row)
    return new_header, new_rows


def apply_derivation(header: list[str], rows: list[dict[str, str]], derivation: Derivation) -> tuple[list[str], list[dict[str, str]]]:
    if isinstance(derivation, EditCellsDerivation):
        return _apply_edit_cells(header, rows, derivation)
    if isinstance(derivation, AddRowDerivation):
        return _apply_add_row(header, rows, derivation)
    if isinstance(derivation, DeleteRowsDerivation):
        return _apply_delete_rows(header, rows, derivation)
    if isinstance(derivation, RecodeDerivation):
        return _apply_recode(header, rows, derivation)
    if isinstance(derivation, DeriveColumnDerivation):
        return _apply_derive_column(header, rows, derivation)
    raise AssertionError(f"unhandled derivation kind {derivation.kind!r}")  # unreachable -- the 5 variants above are exhaustive


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
        source_artifact_id: str | None = None, source_tool_id: str | None = None,
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
            source_artifact_id=source_artifact_id, source_tool_id=source_tool_id,
        )
        d = self._dataset_dir(project_id, meta.dataset_id)
        _atomic_write(d / "v1.csv", csv_bytes)
        _atomic_write(d / "meta.json", json.dumps(meta.model_dump(mode="json"), indent=2, sort_keys=True).encode("utf-8"))
        return meta

    def derive_dataset(self, project_id: str, dataset_id: str, derivation: Derivation, created_at: str) -> DatasetMeta:
        """Always ends with a SECOND dataset on disk (module docstring) --
        its own dataset_id, its own v1.csv, its own sha256, plus
        derived_from_dataset_id/derivation recording what produced it. The
        parent's v1.csv is never opened for writing here; only its
        meta.json gains a superseded_by_dataset_id pointer, so a chart
        computed against the parent's sha256 stays resolvable against the
        exact bytes it was computed from (routes/stats.py's
        dataset_provenance, R-MEA-06) even after this call returns."""
        self.projects.load_project(project_id)  # FileNotFoundError -> 404, same as save_dataset
        parent = self.load_meta(project_id, dataset_id)  # FileNotFoundError -> 404 if the dataset itself is unknown
        rows = self.load_rows(project_id, dataset_id)
        header = [c.name for c in parent.columns]

        new_header, new_rows = apply_derivation(header, rows, derivation)  # ValueError -> 422 at the route layer

        # Carry the parent's effective (possibly user-overridden) column
        # types forward as this rebuild's overrides, so an earlier "Aisle
        # is text, not a number" confirmation survives a derivation instead
        # of being silently re-guessed from scratch (build_columns' own
        # "inferred but user-confirmable" contract). A brand new column
        # (derive_column only) gets no carried-forward override -- it is
        # forced to "text" explicitly rather than left to infer_column_type,
        # which could occasionally guess "numeric" by accident (e.g. a
        # caller-chosen separator="" joining two numeric-looking columns
        # into one numeric-looking string).
        type_overrides = {c.name: c.type for c in parent.columns if c.name in new_header}
        if isinstance(derivation, DeriveColumnDerivation):
            type_overrides[derivation.new_column_name] = "text"
        columns = build_columns(new_header, new_rows, type_overrides)
        quality = scan_quality(columns, new_rows)
        csv_bytes = _rows_to_csv_bytes(new_header, new_rows)

        child = DatasetMeta(
            dataset_id=uuid.uuid4().hex, project_id=project_id, source_filename=parent.source_filename,
            created_at=created_at, sha256=hashlib.sha256(csv_bytes).hexdigest(),
            row_count=len(new_rows), columns=columns, quality=quality,
            derived_from_dataset_id=dataset_id, derivation=derivation,
        )
        child_dir = self._dataset_dir(project_id, child.dataset_id)
        _atomic_write(child_dir / "v1.csv", csv_bytes)
        _atomic_write(child_dir / "meta.json", json.dumps(child.model_dump(mode="json"), indent=2, sort_keys=True).encode("utf-8"))

        # Written last and only after the child fully exists on disk: if
        # this step never ran, the child would just be an unlinked-from-
        # above (but perfectly valid) dataset -- better than a parent
        # claiming a superseding child that failed to actually get written.
        parent.superseded_by_dataset_id = child.dataset_id
        _atomic_write(
            self._dataset_dir(project_id, dataset_id) / "meta.json",
            json.dumps(parent.model_dump(mode="json"), indent=2, sort_keys=True).encode("utf-8"),
        )
        return child

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
