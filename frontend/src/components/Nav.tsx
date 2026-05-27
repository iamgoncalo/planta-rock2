"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/twin", label: "Twin" },
  { href: "/occupation", label: "Ocupação" },
  { href: "/sensors", label: "Sensores" },
  { href: "/shows", label: "Shows" },
  { href: "/chat", label: "Chat" },
  { href: "/ops", label: "Ops" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav
      style={{ backgroundColor: "#1a1f2e", borderBottom: "1px solid #2d3348" }}
      className="sticky top-0 z-50"
    >
      <div className="max-w-screen-xl mx-auto px-4">
        <div className="flex items-center gap-6 h-14">
          {/* Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <div
              style={{ backgroundColor: "#4A7C59" }}
              className="w-7 h-7 rounded flex items-center justify-center text-xs font-bold text-white"
            >
              P
            </div>
            <span
              style={{ color: "#e2e8f0" }}
              className="font-semibold text-sm hidden sm:block"
            >
              PlantaOS
            </span>
            <span
              style={{ color: "#94a3b8" }}
              className="text-xs hidden md:block"
            >
              × Rock in Rio Lisboa 2026
            </span>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto flex-1">
            {TABS.map((tab) => {
              const active =
                pathname === tab.href ||
                (tab.href !== "/" && pathname.startsWith(tab.href));
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  className="px-3 py-1.5 rounded text-sm font-medium transition-colors whitespace-nowrap"
                  style={{
                    backgroundColor: active ? "#4A7C59" : "transparent",
                    color: active ? "#fff" : "#94a3b8",
                  }}
                >
                  {tab.label}
                </Link>
              );
            })}
          </div>

          {/* Public app link */}
          <Link
            href="/app"
            className="shrink-0 px-3 py-1 rounded text-xs font-medium"
            style={{
              backgroundColor: "#2d3348",
              color: "#6FAF82",
              border: "1px solid #4A7C59",
            }}
          >
            App Visitante
          </Link>
        </div>
      </div>
    </nav>
  );
}
