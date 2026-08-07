"""Provenance objects (PLAN §4.5): every computed result is stamped with an
input-data hash, a method identifier, the engine version, assumptions
checked, and warnings -- so an independent reviewer can reproduce any
number the engine produced (COPQ totals now; stability/capability/test
statistics land here in M2+).

`Computed[T]` and `ProvenanceRecord` are frozen (Pydantic `frozen=True`):
assigning a field after construction raises. That closes the *mutation*
path. It cannot, and isn't meant to, stop a caller from fabricating a
`Computed` by calling its constructor directly with made-up numbers --
Pydantic has no notion of a private constructor, and project_store.py
*needs* the public constructor to reconstruct artifacts from saved JSON via
model_validate. The load path has to stay open; only post-construction
mutation is closed. What `compute()` buys is a single place that hashes
the input and stamps the version for every engine-produced number, so code
that skips it is visibly skipping it rather than doing something the
schema silently allowed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel, ConfigDict

from . import __version__

T = TypeVar("T")


def hash_input(data: Any) -> str:
    """Deterministic SHA-256 over JSON-serialized input data."""
    encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_hash: str
    method: str
    engine_version: str
    # Tuples, not lists: frozen=True only blocks *attribute* assignment, so
    # a mutable list field could still be appended to in place. Tuples make
    # "no mutation after construction" true of the whole object, not just
    # its top-level fields.
    assumptions_checked: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class Computed(BaseModel, Generic[T]):
    """A computed value plus the ProvenanceRecord that produced it."""

    model_config = ConfigDict(frozen=True)

    value: T
    provenance: ProvenanceRecord


def compute(
    value: T,
    *,
    method: str,
    input_data: Any,
    assumptions_checked: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> Computed[T]:
    """Stamp a freshly-computed value with a ProvenanceRecord. This is the
    one place in the engine that should construct a ProvenanceRecord for a
    new computation -- loading one back from saved JSON goes through
    model_validate, not here.
    """
    provenance = ProvenanceRecord(
        input_hash=hash_input(input_data),
        method=method,
        engine_version=__version__,
        assumptions_checked=tuple(assumptions_checked),
        warnings=tuple(warnings),
    )
    return Computed(value=value, provenance=provenance)
