"use client";

import { useEffect, useRef, useState } from "react";
import { useApi } from "@/lib/useApi";
import { fmtTime, titleCase } from "@/lib/format";
import type { Overview } from "@/lib/types";
import { IconBell, IconChevron, IconClock, IconSearch } from "./icons";

const PHASE_TONE: Record<string, string> = {
  open: "pill-up",
  pre_open: "pill-warn",
  post_close: "pill",
  closed: "pill-down",
};

export function Topbar() {
  const { data } = useApi<Overview>("/api/overview", 5000);
  const [now, setNow] = useState<string>("");
  const [wsOpen, setWsOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const tick = () => setNow(new Date().toLocaleTimeString("en-IN", { hour12: false }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const phase = data?.session.phase ?? "closed";

  return (
    <header
      style={{
        height: "var(--topbar-h)",
        borderBottom: "1px solid var(--border)",
        background: "rgba(11,15,22,0.82)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "0 22px",
        position: "sticky",
        top: 0,
        zIndex: 20,
      }}
    >
      {/* Search */}
      <div style={{ position: "relative", flex: "0 1 380px" }}>
        <span style={{ position: "absolute", left: 11, top: 9, color: "var(--text-dim)" }}><IconSearch width={16} height={16} /></span>
        <input
          ref={searchRef}
          placeholder="Search strategies, instruments, orders…"
          style={{
            width: "100%",
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            borderRadius: 9,
            padding: "8px 12px 8px 34px",
            color: "var(--text)",
            fontSize: 13,
          }}
        />
        <kbd style={{ position: "absolute", right: 10, top: 8, fontSize: 10.5, color: "var(--text-dim)", border: "1px solid var(--border-strong)", borderRadius: 5, padding: "1px 6px", fontFamily: "var(--font-mono)" }}>
          ⌘K
        </kbd>
      </div>

      <div style={{ flex: 1 }} />

      {/* Session status */}
      <div className="row gap-8">
        <span className={`pill ${PHASE_TONE[phase] ?? "pill"}`}>
          <span className="dot" />NSE · {titleCase(phase)}
        </span>
        <span className="pill mono" title="Local time">
          <IconClock width={13} height={13} /> {now}
        </span>
      </div>

      {/* Workspace selector */}
      <button
        className="btn btn-ghost"
        onClick={() => setWsOpen((v) => !v)}
        style={{ padding: "7px 10px", position: "relative" }}
      >
        <span style={{ width: 8, height: 8, borderRadius: 2, background: "linear-gradient(135deg,var(--accent),var(--accent-2))" }} />
        Trading Desk
        <IconChevron width={15} height={15} />
        {wsOpen && (
          <div className="panel fade-in" style={{ position: "absolute", top: 44, right: 0, width: 210, padding: 6, zIndex: 30 }}>
            {["Trading Desk", "Systematic Alpha", "Risk & Portfolio"].map((w, i) => (
              <div key={w} className="ws-opt" style={{ padding: "9px 10px", borderRadius: 7, fontSize: 13, color: i === 0 ? "var(--text)" : "var(--text-muted)", cursor: "pointer" }}>
                {w}{i === 0 && <span className="pill pill-info" style={{ float: "right", padding: "0 7px" }}>Active</span>}
              </div>
            ))}
          </div>
        )}
      </button>

      {/* Notifications */}
      <button className="btn btn-ghost" style={{ padding: 9, position: "relative" }} onClick={() => setNotifOpen((v) => !v)} aria-label="Notifications">
        <IconBell width={18} height={18} />
        <span style={{ position: "absolute", top: 7, right: 8, width: 7, height: 7, borderRadius: "50%", background: "var(--down)", border: "2px solid var(--bg-1)" }} />
        {notifOpen && (
          <div className="panel fade-in" style={{ position: "absolute", top: 44, right: 0, width: 300, padding: 12, zIndex: 30, textAlign: "left" }}>
            <div className="card-title" style={{ marginBottom: 10 }}>Notifications</div>
            <div className="dim" style={{ fontSize: 12.5, lineHeight: 1.6 }}>
              Data-quality and regime alerts will surface here once thresholds are configured.
              {data && <div style={{ marginTop: 8 }}>Feed healthy · updated {fmtTime(data.as_of)}</div>}
            </div>
          </div>
        )}
      </button>

      {/* Profile */}
      <div className="row gap-8" style={{ paddingLeft: 6, borderLeft: "1px solid var(--border)" }}>
        <div style={{ width: 32, height: 32, borderRadius: 9, background: "linear-gradient(135deg,var(--accent),var(--accent-2))", display: "flex", alignItems: "center", justifyContent: "center", color: "#04121a", fontWeight: 700, fontSize: 13 }}>
          RS
        </div>
      </div>

      <style>{`.ws-opt:hover{background:var(--panel-2);}`}</style>
    </header>
  );
}
