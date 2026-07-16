"""Test fixtures: isolated in-memory DB and a capturing event publisher."""

from __future__ import annotations

import pytest
import pytest_asyncio

from nexus_shared.events.publisher import InMemoryEventPublisher
from research_os.config import Settings
from research_os.container import Container
from research_os.domain.lifecycle import ProjectStatus


@pytest.fixture
def settings() -> Settings:
    return Settings(
        RESEARCH_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        auth_enabled=False,
        review_required=True,
        max_projects_per_user=3,
    )


@pytest.fixture
def publisher() -> InMemoryEventPublisher:
    return InMemoryEventPublisher()


@pytest_asyncio.fixture
async def container(settings, publisher) -> Container:
    c = Container.build(settings, publisher=publisher)
    await c.startup()
    try:
        yield c
    finally:
        await c.shutdown()


async def _create_project(container: Container, name: str = "Momentum Alpha", owner: str = "asha"):
    return await container.projects.create(
        name=name, owner=owner, description="NIFTY momentum study",
        tags=["momentum", "nifty"], metadata={"universe": "NIFTY50"},
    )


async def _create_active_project(container: Container, name: str = "Momentum Alpha"):
    project = await _create_project(container, name)
    await container.hypotheses.create(
        project_id=project.id,
        statement="12-1 momentum predicts next-month returns",
        success_criteria="IC > 0.05 over 5y walk-forward",
    )
    await container.projects.transition(
        project.id, to_status=ProjectStatus.ACTIVE, actor="asha"
    )
    return await container.projects.get(project.id)


@pytest.fixture
def make_project(container):
    """Factory fixture: create a draft project."""
    async def _factory(name: str = "Momentum Alpha", owner: str = "asha"):
        return await _create_project(container, name, owner)
    return _factory


@pytest.fixture
def make_active_project(container):
    """Factory fixture: create a project advanced to Active with one hypothesis."""
    async def _factory(name: str = "Momentum Alpha"):
        return await _create_active_project(container, name)
    return _factory
