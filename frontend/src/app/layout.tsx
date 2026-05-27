import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import StatusBar from "@/components/StatusBar";
import KpiCards from "@/components/KpiCards";

export const metadata: Metadata = {
  title: "PlantaOS × Rock in Rio Lisboa 2026",
  description: "Dashboard operacional de gestão de WCs — Rock in Rio Lisboa 2026",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt">
      <body style={{ backgroundColor: "#0f1117", color: "#e2e8f0", minHeight: "100vh" }}>
        <Nav />
        <StatusBar />
        <KpiCards />
        <main className="max-w-screen-xl mx-auto px-4 py-6">
          {children}
        </main>
      </body>
    </html>
  );
}
