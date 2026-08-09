#!/usr/bin/env python3
"""Turn a golden-harness Coffee Bar run into the drop-in example project.

WHY THIS EXISTS: the first cut of coffee-bar-example-project.zip was the
harness output with the project name patched, and it opened to a project
whose left rail said "Done" on every tool while every form rendered empty
and said "Not saved yet." Both statements were true at once, which is a
uniquely bad way to fail -- the user reasonably concluded the app was
broken.

The cause is that the two writers name artifacts differently:

  * evals/harness/run_goldens.py picks scenario-scoped ids -- coffee-charter,
    coffee-copq, coffee-pilot-round1 -- because goldens from several
    scenarios share one namespace and the ids appear in frozen golden files.
  * every tool form in the desktop app loads ONE hardcoded id: charter,
    copq, pilot-plan (see `const ARTIFACT_ID` in desktop/src/tools/**).

The left rail reads the project's artifact_index by TOOL id, so it sees a
T-03 artifact and prints "Done". The form reads by ARTIFACT id, misses, and
renders its empty state. Nothing is wrong with either lookup on its own.

Renaming the harness ids is not an option -- they are baked into frozen
goldens. So the translation happens here, at the point the example is
packaged, and this script is the record of it.

Two harness artifacts share one tool in three places (COPQ initial + wrap
re-run, pilot rounds 1-2, proof rounds 1-2). Those collapse into versions
of a single artifact rather than being dropped, so the app shows the later
one and the earlier stays readable in version history -- which is what the
project actually did.

Usage:
    python3 examples/make-example-project.py <harness-project-dir> <out-dir>

Regenerate the harness input with:
    SIGMA_PROJECTS_ROOT=/tmp/sigma-example \\
      python3 evals/harness/run_goldens.py --scenario coffee-bar
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

# tool id -> the artifact id that tool's form actually asks for. Mirrors
# `const ARTIFACT_ID` in desktop/src/tools/**; test_example_project.py pins
# the two together so a rename in the app fails a test instead of silently
# emptying this example again.
TOOL_TO_UI_ARTIFACT_ID = {
    "T-01": "picker",
    "T-02": "copq",
    "T-03": "charter",
    "T-04": "sipoc",
    "T-05": "voc-ctq",
    "T-06": "process-map",
    "T-07": "spaghetti",
    "T-08": "checksheet",
    "T-09": "timestudy",
    "T-10": "yieldcalc",
    "T-11": "collection-plan",
    "T-12": "msa",
    "T-15": "fishbone",
    "T-16": "fmea",
    "T-17": "hypothesis",
    "T-18": "solution-matrix",
    "T-19": "pilot-plan",
    "T-20": "proof",
    "T-21": "control-chart",
    "T-22": "control-plan",
    "T-23": "five-s",
    "T-24": "sop",
    "T-25": "a3",
}

# Where two harness artifacts map to one tool, this is the order they become
# versions in: earlier first. Anything not listed sorts by its harness id,
# which is stable but arbitrary -- so keep collisions listed here explicitly
# rather than trusting the sort.
VERSION_ORDER = [
    "coffee-copq",
    "coffee-copq-wrap",
    "coffee-pilot-round1",
    "coffee-pilot-round2",
    "coffee-proof-round1",
    "coffee-proof-round2",
]

PROJECT_ID = "coffee-bar-example"
PROJECT_NAME = "Coffee Bar — worked example"


# Field names whose value is a filename, not a reference. The check sheet's
# dataset export is recorded as
# `source_filename: "coffee-check-sheet-check-sheet.csv"` -- a real file that
# really was written under that name. Rewriting it produces a filename that
# never existed, so these fields get whole-string matching only.
_FILENAME_KEYS = ("filename", "file_name", "path", "source_file")


def _rewrite_ids(node, id_map: dict[str, str], key: str | None = None):
    """Replace old artifact ids anywhere in the tree, not just in the
    artifact_id field.

    Two kinds of citation both have to move, and they need different rules:

    1. REFERENCE FIELDS, where the id is the whole value -- the fishbone's
       evidence `ref`s, the A3's `evidence_ref`s, standard work's
       `linked_control_plan_id`, the dataset metadata's `source_artifact_id`.
       Miss these and the rename leaves them pointing at ids that no longer
       exist: the same empty-screen failure one level deeper.

    2. PROSE, where an id is named inside a sentence -- the wrap-phase COPQ's
       notes say "same rates as the Q2 baseline COPQ (coffee-copq)", the A3
       cites the pilot rounds, standard work cites the control chart. 22 such
       mentions across the project. Leave them and a reader of the example
       chases ids that are not in the app.

    Prose is matched on word boundaries and longest-id-first, so
    `coffee-copq` cannot eat the front of `coffee-copq-wrap`. Filename fields
    are held to whole-string matching (see _FILENAME_KEYS) because a word
    boundary sits happily inside `coffee-check-sheet-check-sheet.csv` and
    would rewrite a real historical filename into a fictional one.
    """
    if isinstance(node, dict):
        return {k: _rewrite_ids(v, id_map, k) for k, v in node.items()}
    if isinstance(node, list):
        return [_rewrite_ids(v, id_map, key) for v in node]
    if isinstance(node, str):
        if node in id_map:
            return id_map[node]
        if key and any(f in key.lower() for f in _FILENAME_KEYS):
            return node
        out = node
        for old in sorted(id_map, key=len, reverse=True):
            out = re.sub(rf"\b{re.escape(old)}\b", id_map[old], out)
        return out
    return node


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not (src / "project.json").is_file():
        print(f"error: {src} has no project.json", file=sys.stderr)
        return 1

    meta = json.loads((src / "project.json").read_text())
    index: dict[str, dict] = meta["artifact_index"]

    # Group harness artifacts by the UI id they belong to, ordered so
    # collisions become v1, v2 in project order.
    def order_key(aid: str) -> tuple[int, str]:
        return (VERSION_ORDER.index(aid) if aid in VERSION_ORDER else 0, aid)

    groups: dict[str, list[str]] = {}
    for aid, entry in sorted(index.items(), key=lambda kv: order_key(kv[0])):
        tool_id = entry["tool_id"]
        ui_id = TOOL_TO_UI_ARTIFACT_ID.get(tool_id)
        if ui_id is None:
            print(f"error: no UI artifact id known for {tool_id} ({aid})", file=sys.stderr)
            return 1
        groups.setdefault(ui_id, []).append(aid)

    id_map = {aid: ui_id for ui_id, aids in groups.items() for aid in aids}

    if dst.exists():
        shutil.rmtree(dst)
    (dst / "artifacts").mkdir(parents=True)
    for extra in ("datasets", "floorplans"):
        if (src / extra).is_dir():
            shutil.copytree(src / extra, dst / extra)
    # Dataset metadata records which artifact produced it
    # (source_artifact_id -- the check sheet exports one), so it needs the
    # same rename as the artifacts. Copying this tree verbatim is what left a
    # dataset pointing at `coffee-check-sheet` after that artifact had become
    # `checksheet`.
    for meta_path in sorted(dst.glob("*/*/meta.json")):
        meta_path.write_text(
            json.dumps(
                _rewrite_ids(json.loads(meta_path.read_text()), id_map),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )

    new_index: dict[str, dict] = {}
    for ui_id, aids in groups.items():
        out_dir = dst / "artifacts" / ui_id
        out_dir.mkdir()
        version = 0
        for aid in aids:
            # A harness artifact can itself have versions; keep them in order
            # and keep numbering upward across the whole group.
            for old_path in sorted(
                (src / "artifacts" / aid).glob("v*.json"),
                key=lambda p: int(p.stem[1:]),
            ):
                version += 1
                body = _rewrite_ids(json.loads(old_path.read_text()), id_map)
                body["artifact_id"] = ui_id
                (out_dir / f"v{version}.json").write_text(
                    json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
                )
        new_index[ui_id] = {
            "latest_version": version,
            "tool_id": index[aids[0]]["tool_id"],
        }

    meta = _rewrite_ids(meta, id_map)
    meta["artifact_index"] = dict(sorted(new_index.items()))
    meta["project_id"] = PROJECT_ID
    meta["name"] = PROJECT_NAME
    (dst / "project.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )

    print(f"wrote {dst} -- {len(new_index)} artifacts, {sum(len(v) for v in groups.values())} source artifacts")
    for ui_id, aids in sorted(groups.items()):
        if len(aids) > 1:
            print(f"  {ui_id}: {' -> v1, '.join(aids)} -> v{len(aids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
