import { ComingSoon } from "@/components/ComingSoon";
import { IconPaper } from "@/components/icons";

export default function Page() {
  return (
    <ComingSoon
      title="Paper Trading"
      spec="SPEC-013"
      icon={<IconPaper width={24} height={24} />}
      tagline="Institutional-grade simulation over live market data."
      description="Paper Trading runs strategies against live prices in a simulated execution environment — virtual capital, realistic slippage, brokerage and taxes, and a full order lifecycle — with no live broker involved. It is the proving ground between backtesting and live execution, and the architecture every future execution feature reuses."
      capabilities={[
        "Virtual portfolios & capital",
        "Market & limit orders",
        "Realistic slippage / fees / latency",
        "Live position & P&L updates",
        "Immutable trade history",
        "Strategy-attributed performance",
      ]}
    />
  );
}
