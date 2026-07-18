import { ComingSoon } from "@/components/ComingSoon";
import { IconExecution } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Execution"
      spec="SPEC-013"
      icon={<IconExecution width={24} height={24} />}
      tagline="Where approved orders become fills."
      description="Execution owns broker abstraction, paper and live trading, execution analytics, and reconciliation. It takes risk-approved orders and works them in the market, measuring slippage and fill quality and reconciling every position back to the broker of record. Execution is deliberately downstream: it acts only on orders that already passed the risk gate."
      capabilities={[
        "Order management system",
        "Broker adapter abstraction",
        "Paper trading",
        "Live execution",
        "Execution quality analytics",
        "Position reconciliation",
      ]}
    />
  );
}
