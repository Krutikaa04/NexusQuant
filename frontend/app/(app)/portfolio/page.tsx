import { ComingSoon } from "@/components/ComingSoon";
import { IconPortfolio } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Portfolio"
      spec="SPEC-011"
      icon={<IconPortfolio width={24} height={24} />}
      tagline="Live capital, positions, and allocation across strategies."
      description="Portfolio owns portfolio state, positions, exposure and correlation, and the capital allocated to each active strategy. It is where the platform's autonomous allocation decisions become real: capital flows to eligible strategies and is withdrawn from paused ones, with every position sized against portfolio-level exposure and drawdown constraints."
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
