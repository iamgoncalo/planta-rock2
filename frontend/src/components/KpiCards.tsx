"use client";

import { useKPIs } from "@/hooks/useKPIs";

interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  sub?: string;
  accent?: string;
}

function KpiCard({ label, value, unit, sub, accent }: KpiCardProps) {
  return (
    <div
      style={{
        backgroundColor: "#1a1f2e",
        border: "1px solid #2d3348",
        borderRadius: 8,
      }}
      className="px-4 py-3 flex-1 min-w-0"
    >
      <p style={{ color: "#94a3b8" }} className="text-xs mb-1 truncate">
        {label}
      </p>
      <p
        className="text-xl font-bold font-mono"
        style={{ color: accent ?? "#e2e8f0" }}
      >
        {value}
        {unit && (
          <span className="text-sm font-normal ml-0.5" style={{ color: "#94a3b8" }}>
            {unit}
          </span>
        )}
      </p>
      {sub && (
        <p style={{ color: "#4b5563" }} className="text-xs mt-0.5 truncate">
          {sub}
        </p>
      )}
    </div>
  );
}

export default function KpiCards() {
  const { kpis, loading } = useKPIs();

  if (loading || !kpis) {
    return (
      <div
        style={{
          backgroundColor: "#13161f",
          borderBottom: "1px solid #2d3348",
        }}
        className="px-4 py-2"
      >
        <div className="max-w-screen-xl mx-auto flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{ backgroundColor: "#1a1f2e", borderRadius: 8 }}
              className="flex-1 h-14 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  const fluxoColor =
    kpis.kpi_01 < 60
      ? "#6FAF82"
      : kpis.kpi_01 < 85
        ? "#D48B3A"
        : "#C25A1A";

  const ocupColor =
    kpis.kpi_02 < 60
      ? "#6FAF82"
      : kpis.kpi_02 < 85
        ? "#D48B3A"
        : "#C25A1A";

  const alertColor =
    kpis.kpi_03 === 0
      ? "#6FAF82"
      : kpis.kpi_03 < 3
        ? "#D48B3A"
        : "#C25A1A";

  return (
    <div
      style={{
        backgroundColor: "#13161f",
        borderBottom: "1px solid #2d3348",
      }}
      className="px-4 py-2"
    >
      <div className="max-w-screen-xl mx-auto flex gap-2">
        <KpiCard
          label="Índice de Fluxo"
          value={kpis.kpi_01.toFixed(0)}
          unit="/100"
          sub="fluxo global"
          accent={fluxoColor}
        />
        <KpiCard
          label="Ocupação Média"
          value={kpis.kpi_02.toFixed(0)}
          unit="%"
          sub="todos os clusters"
          accent={ocupColor}
        />
        <KpiCard
          label="Alertas Críticos"
          value={kpis.kpi_03}
          sub="activos agora"
          accent={alertColor}
        />
        <KpiCard
          label="Redirecionados"
          value={kpis.kpi_04}
          sub="hoje"
          accent="#6FAF82"
        />
      </div>
    </div>
  );
}
