interface Props {
  data: number[];
  width?: number;
  height?: number;
  positive?: boolean;
}

/** A compact area sparkline drawn as pure SVG — no chart library. */
export function Sparkline({ data, width = 108, height = 34, positive }: Props) {
  if (!data || data.length < 2) {
    return <div style={{ width, height }} className="skeleton" />;
  }
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const stepX = width / (data.length - 1);
  const y = (v: number) => height - ((v - min) / span) * (height - 4) - 2;
  const pts = data.map((v, i) => `${(i * stepX).toFixed(2)},${y(v).toFixed(2)}`);
  const up = positive ?? data[data.length - 1] >= data[0];
  const color = up ? "var(--up)" : "var(--down)";
  const id = `sg-${up ? "u" : "d"}`;
  const area = `M0,${height} L${pts.join(" L")} L${width},${height} Z`;

  return (
    <svg width={width} height={height} aria-hidden style={{ display: "block" }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.28" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.6"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
