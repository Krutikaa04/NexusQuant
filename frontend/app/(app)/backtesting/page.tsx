import { ComingSoon } from "@/components/ComingSoon";
import { IconAnalytics } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Backtesting"
      spec="SPEC-009"
      icon={<IconAnalytics width={24} height={24} />}
      tagline="Prove a strategy on history before it risks capital."
      description="Backtesting validates a Strategy Studio strategy against historical market data: deterministic, reproducible runs with walk-forward and Monte-Carlo robustness checks. Results feed the strategy's health score and give the trader evidence — not intuition — before promoting a strategy to paper or live trading."
      capabilities={[
        "Historical backtest engine",
        "Walk-forward validation",
        "Monte-Carlo robustness",
        "Performance & drawdown metrics",
        "Reproducible, deterministic runs",
        "Feeds strategy health scoring",
      ]}
    />
  );
}
