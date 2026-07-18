import { ComingSoon } from "@/components/ComingSoon";
import { IconShield } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Risk"
      spec="SPEC-010"
      icon={<IconShield width={24} height={24} />}
      tagline="The gate every order and allocation must pass."
      description="Risk & Decision Intelligence enforces the limits that make autonomy safe: pre-trade checks, exposure and concentration limits, drawdown control, and the approval gates that decide when a strategy is paused, retired, or requires human sign-off. It produces TradeApproved, TradeRejected, and RebalanceSuggested — the platform never trades around a risk decision."
      capabilities={[
        "Pre-trade limit checks",
        "Exposure & concentration limits",
        "Drawdown & kill-switch control",
        "Autonomous strategy pausing",
        "Human-approval gates",
        "Regime-aware risk posture",
      ]}
    />
  );
}
