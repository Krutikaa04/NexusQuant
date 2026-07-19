import { ComingSoon } from "@/components/ComingSoon";
import { IconDecision } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Decision Intelligence"
      spec="SPEC-010"
      icon={<IconDecision width={24} height={24} />}
      tagline="AI that analyzes and explains — the trader decides."
      description="Decision Intelligence assists the trader by turning market context and strategy signals into explainable recommendations. Every recommendation states the market context, the strategy's confidence, the supporting factors, the identified risks, and a suggested action. The AI analyzes, scores confidence, and highlights risk — but never places an irreversible trade without explicit user approval."
      capabilities={[
        "Market-context assessment",
        "Strategy confidence scoring",
        "Supporting-factor breakdown",
        "Risk identification",
        "Suggested actions (trader-approved)",
        "Fully explainable, human-in-the-loop",
      ]}
    />
  );
}
