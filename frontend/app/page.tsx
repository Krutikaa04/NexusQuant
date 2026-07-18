import Link from "next/link";
import { BrandLockup } from "@/components/Brand";
import { IconArrowRight, IconMarket, IconPulse, IconShield, IconStrategy } from "@/components/icons";

const PILLARS = [
  { icon: <IconStrategy />, title: "The strategy is the product", body: "Every workflow begins with a strategy. The platform decides autonomously which strategies are eligible, funded, paused, or retired — under governance." },
  { icon: <IconShield />, title: "Governed autonomy", body: "No order reaches a broker without passing risk. Every allocation, pause, and retirement is explainable and captured in an immutable audit trail." },
  { icon: <IconPulse />, title: "Deterministic & reproducible", body: "Validated market data and event-sourced pipelines mean any decision — or backtest — can be replayed exactly." },
];

const MODULES = [
  "Markets", "Strategies", "Portfolio", "Orders",
  "Execution", "Risk", "Analytics", "AI Copilot",
];

export default function Landing() {
  return (
    <div style={{ minHeight: "100vh", background: "radial-gradient(140% 90% at 50% -10%, rgba(76,141,255,0.12), transparent 55%), var(--bg-0)" }}>
      {/* Nav */}
      <header className="row between" style={{ padding: "20px 32px", maxWidth: 1200, margin: "0 auto" }}>
        <BrandLockup />
        <div className="row gap-16">
          <a href="https://github.com" className="muted" style={{ fontSize: 13.5 }}>Docs</a>
          <Link href="/dashboard" className="btn btn-primary">
            Launch Platform <IconArrowRight width={16} height={16} />
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section style={{ maxWidth: 1000, margin: "0 auto", padding: "80px 32px 60px", textAlign: "center" }}>
        <div className="pill pill-info fade-up" style={{ marginBottom: 24 }}>
          <span className="dot" />Indian Equity Markets · Institutional Grade
        </div>
        <h1 className="fade-up" style={{ fontSize: 56, lineHeight: 1.05, letterSpacing: "-0.03em", fontWeight: 800, animationDelay: "40ms", maxWidth: 820, margin: "0 auto" }}>
          The autonomous trading platform,{" "}
          <span style={{ background: "linear-gradient(120deg,var(--accent),var(--accent-2))", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>
            engineered like an institution.
          </span>
        </h1>
        <p className="muted fade-up" style={{ fontSize: 18, lineHeight: 1.6, maxWidth: 640, margin: "24px auto 0", animationDelay: "90ms" }}>
          NexusQuant is an institutional-grade autonomous algorithmic trading operating system.
          Strategies are the central entity — the platform decides which to fund, pause, or retire,
          and every order is governed, explainable, and reproducible before it reaches the market.
        </p>
        <div className="row fade-up" style={{ justifyContent: "center", gap: 12, marginTop: 36, animationDelay: "140ms" }}>
          <Link href="/dashboard" className="btn btn-primary" style={{ padding: "12px 22px", fontSize: 14.5 }}>
            Open the Dashboard <IconArrowRight width={17} height={17} />
          </Link>
          <Link href="/market" className="btn" style={{ padding: "12px 22px", fontSize: 14.5 }}>
            <IconMarket width={17} height={17} /> Explore Markets
          </Link>
        </div>
      </section>

      {/* Pillars */}
      <section style={{ maxWidth: 1100, margin: "0 auto", padding: "20px 32px 40px" }}>
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
          {PILLARS.map((p, i) => (
            <div key={p.title} className="panel panel-pad fade-up" style={{ animationDelay: `${180 + i * 70}ms` }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: "var(--accent-soft)", color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16, border: "1px solid rgba(52,226,196,0.22)" }}>
                {p.icon}
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>{p.title}</div>
              <div className="muted" style={{ fontSize: 13.5, lineHeight: 1.65 }}>{p.body}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture strip */}
      <section style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 32px 90px" }}>
        <div className="panel panel-pad fade-up">
          <div className="row between" style={{ marginBottom: 18, flexWrap: "wrap", gap: 8 }}>
            <div>
              <div className="card-title">Strategy-centric architecture</div>
              <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>Bounded contexts, event-driven, one governed path from strategy to execution.</div>
            </div>
            <span className="pill pill-up"><span className="dot" />Markets live</span>
          </div>
          <div className="row" style={{ flexWrap: "wrap", gap: 10 }}>
            {MODULES.map((l, i) => (
              <div key={l} className="row gap-8" style={{ fontSize: 13, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: i < 1 ? "var(--accent-soft)" : "var(--bg-2)", color: i < 1 ? "var(--accent)" : "var(--text-muted)" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, opacity: 0.7 }}>{String(i + 1).padStart(2, "0")}</span>
                {l}
              </div>
            ))}
          </div>
        </div>
        <div className="dim" style={{ textAlign: "center", marginTop: 40, fontSize: 12.5 }}>
          © {new Date().getFullYear()} NexusQuant · Built for systematic traders, portfolio managers, and quant desks.
        </div>
      </section>
    </div>
  );
}
