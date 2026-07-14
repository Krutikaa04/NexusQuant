"""Event Fabric persistence: SQLAlchemy models and async session management.

The fabric owns only the tables defined in SPEC-005 §8 (event_store, consumer_offsets,
event_schema_versions, dead_letter_events). It never reads or writes another context's
schema (SPEC-002 service-boundary rule).
"""
