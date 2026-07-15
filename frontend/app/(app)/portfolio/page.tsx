import { ComingSoon } from "@/components/ComingSoon";
import { IconPortfolio } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Portfolio Intelligence"
      spec="SPEC-011"
      icon={<IconPortfolio width={24} height={24} />}
      tagline="Construction, exposure, and risk under one policy engine."
      description="Portfolio & Risk Intelligence owns portfolio state, position sizing, exposure and correlation analysis, drawdown control, and capital allocation. It enforces risk policy on every proposed trade — producing TradeApproved, TradeRejected, or RebalanceSuggested — so no order reaches execution without passing risk."
      capabilities={[
        "Portfolio construction",
        "Position sizing",
        "Exposure & correlation",
        "Drawdown controls",
        "Capital allocation",
        "Risk-policy enforcement",
      ]}
    />
  );
}
