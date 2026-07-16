"""Development seeding for the Research OS demo workspace.

Creates a small, realistic research portfolio through the *real* SPEC-007 services, so
every rule (lifecycle guards, review gates, event publication) is exercised — nothing is
inserted behind the services' backs. Idempotent: skips when projects already exist.
"""

from __future__ import annotations

import logging

from research_os.container import Container
from research_os.domain.lifecycle import ProjectStatus
from research_os.domain.vocabulary import ExperimentStatus, ReviewDecision

logger = logging.getLogger("nexus.backend.seed_research")


async def seed_research(container: Container) -> None:
    if await _already_seeded(container):
        logger.info("research workspace already seeded; skipping")
        return
    logger.info("seeding research workspace…")

    # 1) A mature momentum project taken through the full governed lifecycle.
    momentum = await container.projects.create(
        name="Cross-Sectional Momentum — NIFTY100",
        owner="asha",
        description=(
            "Cross-sectional 12-1 momentum on the NIFTY100 universe with turnover-aware "
            "position construction. Focus on decay profile and cost sensitivity."
        ),
        tags=["momentum", "cross-sectional", "nifty100"],
        metadata={"universe": "NIFTY100", "horizon": "monthly"},
    )
    h1 = await container.hypotheses.create(
        project_id=momentum.id,
        statement="12-1 month momentum ranks predict next-month cross-sectional returns.",
        success_criteria="Rank IC > 0.05 with t-stat > 2.5 over a 5-year walk-forward.",
        notes="Exclude the most recent month to avoid short-term reversal contamination.",
    )
    await container.hypotheses.create(
        project_id=momentum.id,
        statement="Momentum decays materially beyond 3 months holding.",
        success_criteria="Half-life of alpha < 90 days measured on decile spreads.",
    )
    await container.projects.transition(momentum.id, to_status=ProjectStatus.ACTIVE, actor="asha")
    await container.projects.transition(
        momentum.id, to_status=ProjectStatus.EXPERIMENTING, actor="asha"
    )

    e1 = await container.experiments.create(
        project_id=momentum.id, name="baseline-12-1-deciles",
        dataset_version="nifty100_daily@v3", feature_version="mom_12_1@v1",
        hypothesis_id=h1.id, notes="Equal-weight decile portfolios, monthly rebalance.",
    )
    await container.experiments.start(e1.id)
    await container.experiments.complete(
        e1.id, status=ExperimentStatus.COMPLETED,
        metrics={"rank_ic": 0.061, "t_stat": 2.9, "sharpe": 1.31, "max_dd_pct": -14.2},
    )
    e2 = await container.experiments.create(
        project_id=momentum.id, name="turnover-constrained",
        dataset_version="nifty100_daily@v3", feature_version="mom_12_1@v2",
        hypothesis_id=h1.id, notes="20% monthly turnover cap via rank-buffering.",
    )
    await container.experiments.start(e2.id)
    await container.experiments.complete(
        e2.id, status=ExperimentStatus.COMPLETED,
        metrics={"rank_ic": 0.057, "t_stat": 2.6, "sharpe": 1.42, "max_dd_pct": -11.8},
    )
    await container.reviews.create(
        project_id=momentum.id, reviewer="vikram",
        decision=ReviewDecision.APPROVE,
        comments="IC stable across sub-periods; turnover cap improves net Sharpe. Proceed.",
    )
    await container.projects.transition(
        momentum.id, to_status=ProjectStatus.VALIDATED, actor="asha"
    )
    await container.projects.transition(
        momentum.id, to_status=ProjectStatus.PAPER_TRADING, actor="asha"
    )

    # 2) A mean-reversion project mid-experimentation with a running experiment.
    reversal = await container.projects.create(
        name="Intraday Mean Reversion — Liquid Large-Caps",
        owner="asha",
        description="Short-horizon reversal on the top-20 liquidity bucket using 1-minute bars.",
        tags=["mean-reversion", "intraday"],
        metadata={"universe": "NIFTY50 top-20 by turnover", "horizon": "intraday"},
    )
    hr = await container.hypotheses.create(
        project_id=reversal.id,
        statement="Extreme 30-minute moves partially revert within the same session.",
        success_criteria="Hit rate > 54% and profit factor > 1.3 after 4bps costs.",
    )
    await container.projects.transition(reversal.id, to_status=ProjectStatus.ACTIVE, actor="asha")
    await container.projects.transition(
        reversal.id, to_status=ProjectStatus.EXPERIMENTING, actor="asha"
    )
    e3 = await container.experiments.create(
        project_id=reversal.id, name="zscore-entry-grid",
        dataset_version="nifty50_1min@v1", feature_version="ret_zscore_30m@v1",
        hypothesis_id=hr.id, notes="Grid over entry z in [2.0, 3.5], exit at VWAP.",
    )
    await container.experiments.start(e3.id)  # left running for the demo

    # 3) A fresh volatility project still in draft.
    vol = await container.projects.create(
        name="Volatility Risk Premium — Index Options",
        owner="meera",
        description="Harvesting the gap between implied and realised volatility on NIFTY options.",
        tags=["volatility", "options", "carry"],
        metadata={"universe": "NIFTY index options", "horizon": "weekly"},
    )
    await container.hypotheses.create(
        project_id=vol.id,
        statement="Implied vol systematically exceeds subsequent realised vol ex-events.",
        success_criteria="IV-RV spread positive in >60% of non-event weeks over 3 years.",
    )
    await container.reviews.create(
        project_id=vol.id, reviewer="vikram",
        decision=ReviewDecision.NEEDS_CHANGES,
        comments="Scope the event-exclusion calendar before activation — budget/RBI weeks.",
    )

    logger.info("research workspace seeded")


async def _already_seeded(container: Container) -> bool:
    return len(await container.projects.list()) > 0
