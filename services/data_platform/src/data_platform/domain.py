"""Domain vocabulary for the Data Platform's owned artifacts (SPEC-006 §4, §5).

The three immutable, versioned artifact kinds the Data Platform is the system of record
for. A *single* artifact/version mechanism serves all three because SPEC-006 §5 applies the
identical immutability + append-only-history rule to each.
"""

from __future__ import annotations

from enum import Enum


class ArtifactKind(str, Enum):
    DATASET = "dataset"
    FEATURE = "feature"
    MODEL = "model"


class ArtifactStatus(str, Enum):
    """Lifecycle of a *version*. Versions themselves are immutable; status is metadata."""

    DRAFT = "draft"
    VALIDATED = "validated"
    INDEXED = "indexed"
    RETIRED = "retired"
