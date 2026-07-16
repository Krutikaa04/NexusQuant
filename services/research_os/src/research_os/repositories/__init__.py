"""Repositories — the sole home of SQL/ORM access (SPEC-006 §15 pattern)."""

from research_os.repositories.projects import ProjectRepository
from research_os.repositories.reviews import ReviewRepository

__all__ = ["ProjectRepository", "ReviewRepository"]
