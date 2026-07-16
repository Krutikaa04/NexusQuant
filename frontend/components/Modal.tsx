"use client";

import { useEffect, type ReactNode } from "react";

export function Modal({ title, open, onClose, children, width = 520 }: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  width?: number;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 60,
        background: "rgba(4,7,12,0.72)", backdropFilter: "blur(4px)",
        display: "flex", alignItems: "flex-start", justifyContent: "center",
        padding: "9vh 20px 20px", overflowY: "auto",
      }}
      className="fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="panel fade-up"
        style={{ width: "100%", maxWidth: width, boxShadow: "var(--shadow-lg)" }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="row between" style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
          <span style={{ fontWeight: 700, fontSize: 15 }}>{title}</span>
          <button className="btn btn-ghost" onClick={onClose} aria-label="Close" style={{ padding: "4px 10px" }}>✕</button>
        </div>
        <div style={{ padding: 20 }}>{children}</div>
      </div>
    </div>
  );
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label style={{ display: "block", marginBottom: 14 }}>
      <div className="card-title" style={{ marginBottom: 6 }}>{label}</div>
      {children}
      {hint && <div className="dim" style={{ fontSize: 11.5, marginTop: 4 }}>{hint}</div>}
    </label>
  );
}

export const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-2)",
  border: "1px solid var(--border-strong)",
  borderRadius: 8,
  padding: "9px 12px",
  color: "var(--text)",
  fontSize: 13.5,
  fontFamily: "inherit",
};

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      className="fade-in"
      style={{
        border: "1px solid rgba(255,92,124,0.4)", background: "rgba(255,92,124,0.08)",
        color: "var(--down)", borderRadius: 8, padding: "9px 12px",
        fontSize: 12.5, marginBottom: 14,
      }}
      role="alert"
    >
      {message}
    </div>
  );
}

export function FormSuccess({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      className="fade-in"
      style={{
        border: "1px solid rgba(46,204,155,0.4)", background: "rgba(46,204,155,0.08)",
        color: "var(--up)", borderRadius: 8, padding: "9px 12px",
        fontSize: 12.5, marginBottom: 14,
      }}
    >
      {message}
    </div>
  );
}
