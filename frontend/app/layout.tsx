import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexusQuant — AI-Powered Algorithmic Trading & Decision Intelligence",
  description:
    "AI-powered algorithmic trading and decision intelligence platform for Indian equity traders. Market intelligence, strategy management, backtesting, paper trading and explainable recommendations — with the trader in control.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
