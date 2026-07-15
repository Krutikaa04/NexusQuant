import { ComingSoon } from "@/components/ComingSoon";
import { IconDecision } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Decision Engine"
      spec="SPEC-010"
      icon={<IconDecision width={24} height={24} />}
      tagline="Risk-aware conviction, never a black box."
      description="Decision Intelligence transforms validated alpha into risk-aware investment recommendations. It scores confidence, runs ensemble voting across strategies, and follows the pipeline Signal → Confidence → Portfolio Context → Risk → Recommendation. Every recommendation is explainable and traceable to the research that produced it."
      capabilities={[
        "Confidence scoring",
        "Strategy ensemble voting",
        "Recommendation engine",
        "Strategy ranking",
        "Promotion readiness",
        "Full decision explainability",
      ]}
    />
  );
}
