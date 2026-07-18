import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexusQuant — Autonomous Algorithmic Trading OS",
  description:
    "Institutional-grade autonomous algorithmic trading platform for the Indian equity market. The Strategy is the central entity; every trade is governed, explainable, and reproducible.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
