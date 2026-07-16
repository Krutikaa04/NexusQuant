"""Service/governance tests: rules of SPEC-007 §8 and event publication (§7)."""

from __future__ import annotations

import pytest

from nexus_shared.events.catalog import EventType
from research_os.domain.errors import GovernanceError, ImmutableArtifactError, NotFoundError
from research_os.domain.lifecycle import IllegalTransitionError, ProjectStatus
from research_os.domain.vocabulary import ExperimentStatus, ReviewDecision


# --- projects ---


async def test_create_publishes_event_and_records_history(container, publisher, make_project) -> None:

    project = await make_project()
    assert project.status == "draft"
    events = publisher.of_type(EventType.RESEARCH_PROJECT_CREATED)
    assert len(events) == 1 and events[0].payload["name"] == "Momentum Alpha"
    history = await container.projects.history(project.id)
    assert [h.to_status for h in history] == ["draft"]


async def test_duplicate_name_rejected(container, make_project) -> None:

    await make_project()
    with pytest.raises(GovernanceError, match="already exists"):
        await make_project()


async def test_owner_project_cap_enforced(container, make_project) -> None:

    for i in range(3):  # settings cap = 3
        await make_project(name=f"Project {i}")
    with pytest.raises(GovernanceError, match="limit"):
        await make_project(name="Project 3")


async def test_activation_requires_hypothesis(container, make_project) -> None:

    project = await make_project()
    with pytest.raises(GovernanceError, match="hypothesis"):
        await container.projects.transition(
            project.id, to_status=ProjectStatus.ACTIVE, actor="asha"
        )


async def test_illegal_transition_rejected_by_service(container, make_project) -> None:

    project = await make_project()
    with pytest.raises(IllegalTransitionError):
        await container.projects.transition(
            project.id, to_status=ProjectStatus.VALIDATED, actor="asha"
        )


async def test_full_lifecycle_with_review_gate(container, publisher, make_active_project) -> None:

    project = await make_active_project()

    for step in (
        ProjectStatus.EXPERIMENTING,
        ProjectStatus.VALIDATED,
        ProjectStatus.PAPER_TRADING,
        ProjectStatus.PRODUCTION_CANDIDATE,
    ):
        await container.projects.transition(project.id, to_status=step, actor="asha")

    # Approval without a production_candidate-stage approving review is blocked.
    with pytest.raises(GovernanceError, match="review"):
        await container.projects.transition(
            project.id, to_status=ProjectStatus.APPROVED, actor="asha"
        )

    await container.reviews.create(
        project_id=project.id, reviewer="vik", decision=ReviewDecision.APPROVE,
        comments="Validation metrics meet the bar.",
    )
    await container.projects.transition(
        project.id, to_status=ProjectStatus.APPROVED, actor="asha"
    )

    promoted = publisher.of_type(EventType.STRATEGY_PROMOTED)
    assert len(promoted) == 1
    assert promoted[0].payload["to_status"] == "approved"

    # Approved projects are immutable.
    with pytest.raises(ImmutableArtifactError):
        await container.projects.update(project.id, description="edit after approval")

    # …and can only retire.
    await container.projects.transition(
        project.id, to_status=ProjectStatus.RETIRED, actor="asha"
    )
    final = await container.projects.get(project.id)
    assert final.status == "retired"


async def test_reject_review_does_not_unlock_approval(container, make_active_project) -> None:

    project = await make_active_project()
    for step in (
        ProjectStatus.EXPERIMENTING,
        ProjectStatus.VALIDATED,
        ProjectStatus.PAPER_TRADING,
        ProjectStatus.PRODUCTION_CANDIDATE,
    ):
        await container.projects.transition(project.id, to_status=step, actor="asha")
    await container.reviews.create(
        project_id=project.id, reviewer="vik", decision=ReviewDecision.REJECT,
        comments="Sharpe decays out of sample.",
    )
    with pytest.raises(GovernanceError):
        await container.projects.transition(
            project.id, to_status=ProjectStatus.APPROVED, actor="asha"
        )


# --- hypotheses ---


async def test_hypothesis_crud_and_archive(container, publisher, make_project) -> None:

    project = await make_project()
    h = await container.hypotheses.create(
        project_id=project.id, statement="Momentum persists at 12-1 horizon",
        success_criteria="IC > 0.05", notes="check turnover",
    )
    assert publisher.of_type(EventType.HYPOTHESIS_CREATED)[0].payload["hypothesis_id"] == h.id

    updated = await container.hypotheses.update(h.id, notes="check turnover and costs")
    assert updated.notes == "check turnover and costs"

    archived = await container.hypotheses.update(h.id, archived=True)
    assert archived.archived is True

    # An archived-only project cannot activate.
    with pytest.raises(GovernanceError):
        await container.projects.transition(
            project.id, to_status=ProjectStatus.ACTIVE, actor="asha"
        )


async def test_hypothesis_missing_project_404s(container) -> None:
    with pytest.raises(NotFoundError):
        await container.hypotheses.create(
            project_id="nope", statement="Long enough statement", success_criteria="x"
        )


# --- experiments ---


async def test_experiment_flow_and_events(container, publisher, make_active_project) -> None:

    project = await make_active_project()
    exp = await container.experiments.create(
        project_id=project.id, name="baseline-momentum",
        dataset_version="nifty_daily@v3", feature_version="mom_12_1@v1",
    )
    assert exp.status == "pending"

    started = await container.experiments.start(exp.id)
    assert started.status == "running" and started.started_at is not None
    assert publisher.of_type(EventType.EXPERIMENT_STARTED)[0].payload["experiment_id"] == exp.id

    done = await container.experiments.complete(
        exp.id, status=ExperimentStatus.COMPLETED, metrics={"sharpe": 1.4, "ic": 0.07}
    )
    assert done.metrics["sharpe"] == 1.4
    completed_events = publisher.of_type(EventType.EXPERIMENT_COMPLETED)
    assert completed_events[0].payload["metrics"]["ic"] == 0.07

    # Terminal is final.
    with pytest.raises(GovernanceError):
        await container.experiments.complete(
            exp.id, status=ExperimentStatus.FAILED, metrics={}
        )


async def test_experiment_requires_experimentation_status(container, make_project) -> None:

    project = await make_project()  # still draft
    with pytest.raises(GovernanceError, match="active or"):
        await container.experiments.create(
            project_id=project.id, name="too-early",
            dataset_version="d@v1", feature_version="f@v1",
        )


async def test_experiment_requires_explicit_versions(container, make_active_project) -> None:

    project = await make_active_project()
    with pytest.raises(GovernanceError, match="versions"):
        await container.experiments.create(
            project_id=project.id, name="no-versions",
            dataset_version="  ", feature_version="f@v1",
        )


async def test_cannot_complete_unstarted_experiment(container, make_active_project) -> None:

    project = await make_active_project()
    exp = await container.experiments.create(
        project_id=project.id, name="x", dataset_version="d@v1", feature_version="f@v1"
    )
    with pytest.raises(GovernanceError, match="running"):
        await container.experiments.complete(
            exp.id, status=ExperimentStatus.COMPLETED, metrics={}
        )


# --- reviews ---


async def test_review_published_and_immutable_by_construction(container, publisher, make_active_project) -> None:

    project = await make_active_project()
    review = await container.reviews.create(
        project_id=project.id, reviewer="vik",
        decision=ReviewDecision.NEEDS_CHANGES, comments="Add turnover analysis.",
    )
    assert review.stage == "active"
    events = publisher.of_type(EventType.RESEARCH_REVIEWED)
    assert events[0].payload["decision"] == "needs_changes"
    # The repository exposes no update/delete for reviews — immutability by construction.
    from research_os.repositories.reviews import ReviewRepository

    assert not hasattr(ReviewRepository, "update_review")
    assert not hasattr(ReviewRepository, "delete")


async def test_review_requires_comments(container, make_active_project) -> None:

    project = await make_active_project()
    with pytest.raises(GovernanceError, match="comments"):
        await container.reviews.create(
            project_id=project.id, reviewer="vik",
            decision=ReviewDecision.APPROVE, comments="   ",
        )
