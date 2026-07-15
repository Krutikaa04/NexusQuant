"use client";

import { useEffect, useRef, useState } from "react";
import { fmtNum } from "@/lib/format";

/** A price that briefly flashes green/red when it ticks up/down — the live-terminal feel. */
export function PriceCell({ value, dp = 2 }: { value: number | null; dp?: number }) {
  const prev = useRef<number | null>(null);
  const [flash, setFlash] = useState<"" | "flash-up" | "flash-down">("");

  useEffect(() => {
    if (value !== null && prev.current !== null && value !== prev.current) {
      setFlash(value > prev.current ? "flash-up" : "flash-down");
      const id = setTimeout(() => setFlash(""), 600);
      prev.current = value;
      return () => clearTimeout(id);
    }
    prev.current = value;
  }, [value]);

  return (
    <span className={`mono ${flash}`} style={{ padding: "2px 4px", borderRadius: 4 }}>
      {fmtNum(value, dp)}
    </span>
  );
}
