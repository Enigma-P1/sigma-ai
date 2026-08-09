"""Determinism: canonical JSON + the volatile-field normalizer.

The engine is deterministic everywhere except two server-generated ids
(confirmed by reading the engine source, not assumed): `dataset_id`
(routes/datasets.py, `uuid.uuid4().hex`) and `image_id`
(routes/floorplans.py, `uuid.uuid4().hex`). Every timestamp in this
engine is caller-supplied (base.py's validate_iso8601 pattern -- never
`datetime.now()` server-side, per that module's own docstring and every
route module's comments), and every provenance hash is computed from
DATA VALUES, never from either volatile id -- so a scenario driver that
hardcodes its own timestamps (as these all do) needs no timestamp
normalizing at all. This module still exposes NORMALIZED_KEYS as the one
place that fact is asserted, so a future volatile field has one obvious
place to be added.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

# Key names whose string VALUE is server-generated and non-deterministic
# across runs (uuid4().hex), wherever they appear in a response body --
# by key name, not by pattern-matching the value shape, so the rule stays
# readable and auditable against the two route modules cited above.
# `folder_path` is machine-dependent rather than run-dependent: the
# project-info route echoes the store's absolute on-disk path, which
# differs between the freeze machine and any other machine (CI run 33
# failed on exactly this -- /root/.sigma-ai vs /home/runner/.sigma-ai).
NORMALIZED_KEYS: frozenset[str] = frozenset({"dataset_id", "image_id", "folder_path"})

# Defense in depth for the key-based rule above: a scenario driver that
# threads a freshly-minted dataset_id/image_id into some OTHER field (e.g.
# an A3 panel's freeform `seeded_from.artifact_ref`, echoing "which
# dataset this came from") would otherwise leak that run's random id into
# the golden under a key NORMALIZED_KEYS doesn't know about. uuid4().hex
# is exactly 32 lowercase hex characters -- distinct in shape from every
# other id/hash this engine produces (sha256 hex digests are 64 chars;
# every caller-chosen artifact_id/project_id in this harness is a short
# human-readable slug like "s1-charter", never bare hex) -- so matching
# the VALUE SHAPE, everywhere, is a safe supplement, not just the exact
# known field names.
_UUID4_HEX = re.compile(r"^[0-9a-f]{32}$")

PLACEHOLDER = "<normalized>"


def _normalize_value(key: str | int | None, v: Any) -> Any:
    if isinstance(v, str) and v:
        if (isinstance(key, str) and key in NORMALIZED_KEYS) or _UUID4_HEX.match(v):
            return PLACEHOLDER
    return normalize(v)


def normalize(obj: Any) -> Any:
    """Recursively replace every non-empty string value at a NORMALIZED_KEYS
    key -- or that simply LOOKS like a uuid4().hex, regardless of key name
    (see _UUID4_HEX above) -- anywhere in the tree, with a stable
    placeholder. Leaves everything else (including sha256 hashes, which
    are deterministic functions of fixed file content, and every
    provenance input_hash, which hashes data values never a volatile id)
    untouched."""
    if isinstance(obj, dict):
        return {k: _normalize_value(k, v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_value(None, v) for v in obj]
    return obj


def canonical_json_bytes(obj: Any) -> bytes:
    """Sorted keys, fixed indent, deterministic float formatting (Python's
    json module renders floats via float.__repr__ -- the shortest string
    that round-trips to the exact same IEEE-754 double, which is itself a
    deterministic function of the bit pattern, not of formatting options).
    One trailing newline so files diff cleanly and every writer in this
    package always ends a file exactly the same way."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def canonicalize_for_golden(obj: Any) -> Any:
    """normalize() then round-trip through canonical JSON so the returned
    object's own key order/float formatting is exactly what writing it
    would produce -- used so in-memory diffing (replay mode) compares
    against the identical representation freeze mode wrote to disk."""
    return json.loads(canonical_json_bytes(normalize(obj)))


def hash_value(obj: Any) -> str:
    """SHA-256 over an object's canonical (normalized) JSON bytes -- used
    for the manifest's per-step input_hash. Deliberately reuses
    canonical_json_bytes(normalize(...)) so a step's recorded input hash
    never shifts just because a fresh dataset_id/image_id was minted this
    run."""
    return hashlib.sha256(canonical_json_bytes(normalize(obj))).hexdigest()
