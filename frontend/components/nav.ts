import type { ComponentType, SVGProps } from "react";
import {
  IconAnalytics,
  IconCopilot,
  IconExecution,
  IconGrid,
  IconMarket,
  IconOrders,
  IconPortfolio,
  IconSettings,
  IconShield,
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

// Autonomous Algorithmic Trading OS navigation. The Strategy is the central entity;
// every capital-facing module operates on strategies and their allocations.
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
      { href: "/strategies", label: "Strategies", icon: IconStrategy, status: "soon", spec: "SPEC-008" },
      { href: "/portfolio", label: "Portfolio", icon: IconPortfolio, status: "soon", spec: "SPEC-011" },
      { href: "/orders", label: "Orders", icon: IconOrders, status: "soon", spec: "SPEC-013" },
      { href: "/execution", label: "Execution", icon: IconExecution, status: "soon", spec: "SPEC-013" },
    ],
  },
  {
    title: "Control",
    items: [
      { href: "/risk", label: "Risk", icon: IconShield, status: "soon", spec: "SPEC-010" },
      { href: "/analytics", label: "Analytics", icon: IconAnalytics, status: "soon", spec: "SPEC-009" },
      { href: "/copilot", label: "AI Copilot", icon: IconCopilot, status: "soon", spec: "SPEC-012" },
      { href: "/settings", label: "Settings", icon: IconSettings, status: "live" },
    ],
  },
];
