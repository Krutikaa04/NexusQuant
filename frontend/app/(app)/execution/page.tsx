import { ComingSoon } from "@/components/ComingSoon";
import { IconExecution } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Execution Center"
      spec="SPEC-013"
      icon={<IconExecution width={24} height={24} />}
      tagline="Optional automated execution — always trader-approved."
      description="The Execution Center owns broker abstraction, order routing, execution analytics, and reconciliation. It works trader-approved orders in the market, measuring slippage and fill quality and reconciling every position back to the broker of record. Automated execution is optional and the trader stays in control — nothing irreversible happens without explicit approval."
      capabilities={[
        "Broker adapter abstraction",
        "Order routing & management",
        "Optional automated execution",
        "Execution quality analytics",
        "Position reconciliation",
        "Trader-approved, human-in-the-loop",
      ]}
    />
  );
}
