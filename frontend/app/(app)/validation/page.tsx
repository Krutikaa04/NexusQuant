import { ComingSoon } from "@/components/ComingSoon";
import { IconValidation } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Validation Platform"
      spec="SPEC-009"
      icon={<IconValidation width={24} height={24} />}
      tagline="Statistical proof before capital is ever at risk."
      description="The Validation Platform subjects every candidate strategy to rigorous statistical scrutiny — event-driven backtesting, walk-forward analysis, and Monte-Carlo simulation — using the immutable, corporate-action-adjusted market data from the Market Intelligence layer. No strategy is promoted without passing validation."
      capabilities={[
        "Event-driven backtesting",
        "Walk-forward analysis",
        "Monte-Carlo simulation",
        "Out-of-sample validation",
        "Overfitting & bias detection",
        "Deterministic, replayable results",
      ]}
    />
  );
}
