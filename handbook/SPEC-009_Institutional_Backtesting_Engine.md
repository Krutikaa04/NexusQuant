
# SPEC-009 — Institutional Backtesting Engine
Version: 1.0

## Executive Summary
The Backtesting Engine is the validation layer between research and live execution.
It must faithfully replay historical markets, simulate realistic execution, and
produce reproducible performance metrics.

# 1. Objectives
- Deterministic replay
- Realistic execution simulation
- Walk-forward validation
- Parameter optimization
- Comparable experiment outputs

# 2. Architecture

```mermaid
flowchart LR
A[Historical Data]
-->B[Replay Engine]
-->C[Strategy SDK]
-->D[Execution Simulator]
-->E[Portfolio Simulator]
-->F[Metrics Engine]
-->G[Research Report]
```

# 3. Core Components
- Replay Scheduler
- Event Dispatcher
- Strategy Runtime
- Broker Simulator
- Portfolio Simulator
- Metrics Engine
- Report Generator

# 4. Replay Modes
- Tick Replay
- Candle Replay
- Accelerated Replay
- Step-by-step Debug Replay

# 5. Execution Simulation
Supports:
- Market Orders
- Limit Orders
- Stop Orders
- Partial Fills
- Slippage
- Brokerage
- Exchange Fees
- Latency

# 6. Portfolio Accounting
Tracks:
- Cash
- Equity
- Unrealized PnL
- Realized PnL
- Margin
- Buying Power

# 7. Performance Metrics
Returns:
- CAGR
- Annual Return
- Daily Return

Risk:
- Sharpe
- Sortino
- Calmar
- Max Drawdown
- VaR

Trade:
- Win Rate
- Profit Factor
- Expectancy
- Average Holding Time

# 8. Validation
- Walk-forward Analysis
- Rolling Windows
- Expanding Windows
- Monte Carlo Resampling

# 9. APIs
POST /api/v1/backtests
GET /api/v1/backtests/{id}
GET /api/v1/backtests/{id}/metrics
GET /api/v1/backtests/{id}/report

# 10. Testing
Unit:
- Replay ordering
- Portfolio accounting
- Slippage

Integration:
- End-to-end replay

Regression:
- Benchmark datasets

# 11. Acceptance Criteria
- Identical replay yields identical results
- Metrics validated
- Reports reproducible
- APIs documented

# 12. Claude Code Guidance
Backtests are read-only consumers of historical data.
No backtest may mutate production datasets.
Every report must include configuration, dataset version and strategy version.
