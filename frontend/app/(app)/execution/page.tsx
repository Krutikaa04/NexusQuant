import { ComingSoon } from "@/components/ComingSoon";
import { IconExecution } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Execution & OMS"
      spec="SPEC-013"
      icon={<IconExecution width={24} height={24} />}
      tagline="Governed execution — the final, downstream capability."
      description="Execution Intelligence owns the order management system, broker abstraction, paper and live trading, execution analytics, and reconciliation. Trading is deliberately the last capability in the platform: every production order must originate from validated research and pass risk approval before it reaches a broker."
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
