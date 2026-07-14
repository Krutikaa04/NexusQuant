"""NexusQuant Data Platform & Knowledge Layer (SPEC-006).

Canonical persistence: the migration authority, the immutable versioned artifact store
(datasets / features / models), data lineage, read models, and the Redis cache. Owns
storage and versioning, never business logic (SPEC-006 §2).
"""

__version__ = "0.1.0"
