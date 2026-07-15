import { ComingSoon } from "@/components/ComingSoon";
import { IconAlpha } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Alpha Factory"
      spec="SPEC-008"
      icon={<IconAlpha width={24} height={24} />}
      tagline="Feature engineering and alpha generation at institutional rigor."
      description="The Alpha Factory owns the indicator engine, feature engineering, the feature store, and alpha generation. Features and models are versioned, immutable artifacts with full lineage back to the datasets they were engineered from — so every signal is reproducible and auditable."
      capabilities={[
        "Indicator & feature engine",
        "Versioned feature store",
        "Alpha signal generation",
        "Feature lineage & lookback safety",
        "ML pipeline integration",
        "Reproducible model artifacts",
      ]}
    />
  );
}
