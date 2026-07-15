import { ComingSoon } from "@/components/ComingSoon";
import { IconResearch } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Research OS"
      spec="SPEC-007"
      icon={<IconResearch width={24} height={24} />}
      tagline="The governed workspace where every strategy begins its life."
      description="The Research Operating System is the central workspace for all quantitative research. Every strategy starts as a research project and moves through a governed lifecycle — draft, active, experimenting, validated, paper trading, production candidate, approved — with review events gating each transition. Approved research artifacts become immutable."
      capabilities={[
        "Research projects & hypotheses",
        "Version-aware experiments",
        "Dataset & feature lineage",
        "Peer review workflow",
        "Promotion pipeline to production",
        "Immutable approved artifacts",
      ]}
    />
  );
}
