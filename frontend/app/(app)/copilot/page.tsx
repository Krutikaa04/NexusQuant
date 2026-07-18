import { ComingSoon } from "@/components/ComingSoon";
import { IconCopilot } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="AI Copilot"
      spec="SPEC-012"
      icon={<IconCopilot width={24} height={24} />}
      tagline="Explains and reviews every autonomous decision."
      description="The AI Copilot narrates the platform's autonomy through documented APIs only — never owning business rules. It explains why a strategy was allocated capital, paused, or retired, reviews strategy logic and risk posture, generates daily trading reports, and answers questions across every domain. It reads widely but acts through published contracts, so it can never bypass governance."
      capabilities={[
        "Autonomous-decision narration",
        "Strategy & risk review",
        "Plain-language explainability",
        "Daily trading reports",
        "Cross-domain Q&A",
        "API-only, no hidden rules",
      ]}
    />
  );
}
