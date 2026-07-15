import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexusQuant — Institutional Quant Research OS",
  description:
    "Institutional-grade Quantitative Research & Execution Platform for the Indian equity market. Research is the product.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
