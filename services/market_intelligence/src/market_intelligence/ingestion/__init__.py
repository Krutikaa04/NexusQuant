"""Market-data ingestion pipeline (SPEC-004 Core Architecture).

Exchange Feed → Vendor Adapter → Collector → Validator → Normalizer → Data Quality Engine
→ Market Intelligence Store → Event Publisher.
"""
