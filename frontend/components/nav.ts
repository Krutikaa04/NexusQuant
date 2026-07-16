import type { ComponentType, SVGProps } from "react";
import {
  IconAlpha,
  IconCopilot,
  IconDecision,
  IconExecution,
  IconGrid,
  IconMarket,
  IconPortfolio,
  IconResearch,
  IconSettings,
  IconSystem,
  IconValidation,
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

export const NAV: NavSection[] = [
  {
    title: "Overview",
    items: [{ href: "/dashboard", label: "Dashboard", icon: IconGrid, status: "live" }],
  },
  {
    title: "Research Pipeline",
    items: [
      { href: "/market", label: "Market Intelligence", icon: IconMarket, status: "live", spec: "SPEC-004" },
      { href: "/research", label: "Research OS", icon: IconResearch, status: "live", spec: "SPEC-007" },
      { href: "/alpha", label: "Alpha Factory", icon: IconAlpha, status: "soon", spec: "SPEC-008" },
      { href: "/validation", label: "Validation", icon: IconValidation, status: "soon", spec: "SPEC-009" },
    ],
  },
  {
    title: "Capital",
    items: [
      { href: "/decision", label: "Decision Engine", icon: IconDecision, status: "soon", spec: "SPEC-010" },
      { href: "/portfolio", label: "Portfolio", icon: IconPortfolio, status: "soon", spec: "SPEC-011" },
      { href: "/execution", label: "Execution & OMS", icon: IconExecution, status: "soon", spec: "SPEC-013" },
    ],
  },
  {
    title: "Platform",
    items: [
      { href: "/copilot", label: "AI Copilot", icon: IconCopilot, status: "soon", spec: "SPEC-012" },
      { href: "/system", label: "System", icon: IconSystem, status: "live" },
      { href: "/settings", label: "Settings", icon: IconSettings, status: "live" },
    ],
  },
];
