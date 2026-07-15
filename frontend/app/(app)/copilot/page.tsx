import { ComingSoon } from "@/components/ComingSoon";
import { IconCopilot } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="AI Quant Copilot"
      spec="SPEC-012"
      icon={<IconCopilot width={24} height={24} />}
      tagline="A research assistant that explains, reviews, and reports."
      description="The AI Quant Copilot assists research through documented APIs only — never owning business rules. It reviews strategies, explains decisions in plain language, generates daily reports and documentation, and helps researchers navigate the platform. It reads across every domain but acts through published contracts."
      capabilities={[
        "Research assistant",
        "Strategy & code review",
        "Decision explainability",
        "Daily report generation",
        "Documentation authoring",
        "API-only, no hidden rules",
      ]}
    />
  );
}
