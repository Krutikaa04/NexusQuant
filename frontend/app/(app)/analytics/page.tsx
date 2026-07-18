import { ComingSoon } from "@/components/ComingSoon";
import { IconAnalytics } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Analytics"
      spec="SPEC-009"
      icon={<IconAnalytics width={24} height={24} />}
      tagline="Proof that a strategy deserves capital."
      description="Analytics owns statistical validation and performance attribution: backtesting, walk-forward, and Monte-Carlo analysis, plus live attribution of realized P&L back to strategies, regimes, and instruments. Every result is deterministic and reproducible from immutable market data, so a strategy's health score and eligibility rest on evidence, not intuition."
      capabilities={[
        "Backtesting engine",
        "Walk-forward validation",
        "Monte-Carlo robustness",
        "Performance attribution",
        "Strategy health scoring",
        "Reproducible, deterministic runs",
      ]}
    />
  );
}
