export function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden>
      <defs>
        <linearGradient id="nqg" x1="0" y1="0" x2="40" y2="40">
          <stop offset="0" stopColor="#34e2c4" />
          <stop offset="1" stopColor="#4c8dff" />
        </linearGradient>
      </defs>
      <rect x="1.5" y="1.5" width="37" height="37" rx="10" stroke="url(#nqg)" strokeWidth="2" />
      <path d="M12 28V12l16 16V12" stroke="url(#nqg)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="28" cy="12" r="2.4" fill="#34e2c4" />
    </svg>
  );
}

export function BrandLockup({ compact = false }: { compact?: boolean }) {
  return (
    <div className="row gap-12" style={{ alignItems: "center" }}>
      <BrandMark size={compact ? 26 : 30} />
      {!compact && (
        <div style={{ lineHeight: 1.1 }}>
          <div style={{ fontWeight: 700, letterSpacing: "-0.01em", fontSize: 16 }}>
            Nexus<span style={{ color: "var(--accent)" }}>Quant</span>
          </div>
          <div className="dim" style={{ fontSize: 10.5, letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Autonomous Trading OS
          </div>
        </div>
      )}
    </div>
  );
}
