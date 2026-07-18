import { ComingSoon } from "@/components/ComingSoon";
import { IconOrders } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Orders"
      spec="SPEC-013"
      icon={<IconOrders width={24} height={24} />}
      tagline="The order lifecycle, from intent to broker."
      description="Orders owns the order management surface: every order originates from a strategy's allocation decision, is validated against risk limits, routed through the broker abstraction, and tracked through its full lifecycle. Order state is event-sourced and auditable end-to-end — no order reaches a broker without passing the risk gate."
      capabilities={[
        "Strategy-originated order intent",
        "Order state machine & lifecycle",
        "Pre-trade risk validation",
        "Broker-agnostic routing",
        "Amend / cancel / replace",
        "Immutable order audit trail",
      ]}
    />
  );
}
