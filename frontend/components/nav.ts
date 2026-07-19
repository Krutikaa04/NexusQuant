import type { ComponentType, SVGProps } from "react";
import {
  IconAnalytics,
  IconCopilot,
  IconDecision,
  IconExecution,
  IconGrid,
  IconMarket,
  IconPaper,
  IconPortfolio,
  IconSettings,
  IconStrategy,
} from "./icons";

export interface NavItem {
  href: string;
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  status: "live" | "soon";
  spec?: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

// AI-powered Algorithmic Trading & Decision Intelligence Platform. The trader stays in
// control; the Strategy Studio is the core workspace and Decision Intelligence assists.
export const NAV: NavSection[] = [
  {
    title: "Overview",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: IconGrid, status: "live" },
      { href: "/market", label: "Markets", icon: IconMarket, status: "live", spec: "SPEC-004" },
    ],
  },
  {
    title: "Trading",
    items: [
      { href: "/strategies", label: "Strategy Studio", icon: IconStrategy, status: "live", spec: "SPEC-008" },
      { href: "/backtesting", label: "Backtesting", icon: IconAnalytics, status: "soon", spec: "SPEC-009" },
      { href: "/paper", label: "Paper Trading", icon: IconPaper, status: "soon", spec: "SPEC-013" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { href: "/decision", label: "Decision Intelligence", icon: IconDecision, status: "soon", spec: "SPEC-010" },
      { href: "/portfolio", label: "Portfolio", icon: IconPortfolio, status: "soon", spec: "SPEC-011" },
    ],
  },
  {
    title: "Platform",
    items: [
      { href: "/execution", label: "Execution Center", icon: IconExecution, status: "soon", spec: "SPEC-013" },
      { href: "/copilot", label: "AI Copilot", icon: IconCopilot, status: "soon", spec: "SPEC-012" },
      { href: "/settings", label: "Settings", icon: IconSettings, status: "live" },
    ],
  },
];
