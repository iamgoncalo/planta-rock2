"use client";

import { useClusters } from "@/hooks/useClusters";
import { useKPIs } from "@/hooks/useKPIs";
import { useCurrentShow } from "@/hooks/useCurrentShow";
import ParqueTejo from "@/components/twin/ParqueTejo";

export default function TwinPage() {
  const { clusters, loading, error, wsStatus } = useClusters();
  const { kpis } = useKPIs();
  const { show_activo, minutos_para_headliner } = useCurrentShow();

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
            Digital Twin — Parque Tejo
          </h1>
          <p className="text-sm" style={{ color: "#94a3b8" }}>
            Visão em tempo real de todos os clusters WC
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            style={{
              backgroundColor:
                wsStatus === "connected"
                  ? "#4A7C5922"
                  : wsStatus === "connecting"
                    ? "#D48B3A22"
                    : "#6B728022",
              color:
                wsStatus === "connected"
                  ? "#6FAF82"
                  : wsStatus === "connecting"
                    ? "#D48B3A"
                    : "#6B7280",
              border: `1px solid ${
                wsStatus === "connected"
                  ? "#4A7C59"
                  : wsStatus === "connecting"
                    ? "#D48B3A"
                    : "#6B7280"
              }`,
              padding: "2px 8px",
              borderRadius: 4,
            }}
          >
            WS{" "}
            {wsStatus === "connected"
              ? "conectado"
              : wsStatus === "connecting"
                ? "a conectar..."
                : "offline"}
          </span>
        </div>
      </div>

      {error && (
        <div
          className="mb-4 p-3 rounded-lg text-sm"
          style={{
            backgroundColor: "#C25A1A22",
            border: "1px solid #C25A1A44",
            color: "#C25A1A",
          }}
        >
          Backend offline ou inacessível — {error}
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-4">
        {/* Map */}
        <div className="flex-1">
          {loading ? (
            <div
              style={{
                backgroundColor: "#1a1f2e",
                border: "1px solid #2d3348",
                borderRadius: 12,
                height: 400,
              }}
              className="animate-pulse flex items-center justify-center"
            >
              <span style={{ color: "#4b5563" }}>A carregar mapa...</span>
            </div>
          ) : (
            <ParqueTejo clusters={clusters} />
          )}
        </div>

        {/* Right sidebar */}
        <div className="w-full lg:w-64 flex flex-col gap-3">
          {/* Show banner */}
          <div
            style={{
              backgroundColor: "#1a1f2e",
              border: "1px solid #2d3348",
              borderRadius: 8,
              padding: 12,
            }}
          >
            <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: "#94a3b8" }}>
              Show Activo
            </p>
            {show_activo ? (
              <>
                <p className="font-bold" style={{ color: "#6FAF82" }}>
                  ♪ {show_activo}
                </p>
                {minutos_para_headliner !== null && minutos_para_headliner > 0 && (
                  <p className="text-xs mt-1" style={{ color: "#D48B3A" }}>
                    Headliner em {minutos_para_headliner} min
                  </p>
                )}
              </>
            ) : (
              <p style={{ color: "#4b5563" }} className="text-sm">
                Sem show activo
              </p>
            )}
          </div>

          {/* KPI mini */}
          {kpis && (
            <div
              style={{
                backgroundColor: "#1a1f2e",
                border: "1px solid #2d3348",
                borderRadius: 8,
                padding: 12,
              }}
              className="flex flex-col gap-2 text-xs"
            >
              <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "#94a3b8" }}>
                KPIs Globais
              </p>
              <div className="flex justify-between">
                <span style={{ color: "#94a3b8" }}>Fluxo</span>
                <span className="font-mono font-bold" style={{ color: "#e2e8f0" }}>
                  {kpis.kpi_01.toFixed(0)}/100
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "#94a3b8" }}>Ocupação</span>
                <span className="font-mono font-bold" style={{ color: "#e2e8f0" }}>
                  {kpis.kpi_02.toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "#94a3b8" }}>Alertas</span>
                <span
                  className="font-mono font-bold"
                  style={{
                    color: kpis.kpi_03 > 0 ? "#C25A1A" : "#6FAF82",
                  }}
                >
                  {kpis.kpi_03}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "#94a3b8" }}>Redireccionados</span>
                <span className="font-mono font-bold" style={{ color: "#e2e8f0" }}>
                  {kpis.kpi_04}
                </span>
              </div>
            </div>
          )}

          {/* Cluster status list */}
          <div
            style={{
              backgroundColor: "#1a1f2e",
              border: "1px solid #2d3348",
              borderRadius: 8,
              padding: 12,
            }}
          >
            <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "#94a3b8" }}>
              Estado Clusters
            </p>
            {clusters.map((c) => {
              const sections = Object.values(c.secoes).filter(Boolean);
              const avgOcc =
                sections.length > 0
                  ? sections.reduce((s, sec) => s + (sec?.ocupacao_pct ?? 0), 0) /
                    sections.length
                  : 0;
              const worstOrder: Record<string, number> = {
                critico: 0, cheio: 1, moderado: 2, livre: 3, offline: 4,
              };
              const worstStatus =
                sections.sort(
                  (a, b) =>
                    (worstOrder[a?.status ?? "offline"] ?? 5) -
                    (worstOrder[b?.status ?? "offline"] ?? 5)
                )[0]?.status ?? "offline";

              const color =
                worstStatus === "critico"
                  ? "#C25A1A"
                  : worstStatus === "cheio" || worstStatus === "moderado"
                    ? "#D48B3A"
                    : worstStatus === "livre"
                      ? "#6FAF82"
                      : "#6B7280";

              return (
                <div
                  key={c.cluster_id}
                  className="flex items-center justify-between py-1 text-xs"
                  style={{ borderBottom: "1px solid #1e2330" }}
                >
                  <span style={{ color: "#e2e8f0" }}>{c.cluster_id}</span>
                  <span className="font-mono" style={{ color }}>
                    {avgOcc.toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom show banner */}
      {show_activo && (
        <div
          className="mt-4 p-3 rounded-lg flex items-center gap-3"
          style={{
            backgroundColor: "#1e2a1e",
            border: "1px solid #4A7C59",
          }}
        >
          <span style={{ color: "#6FAF82" }}>♪</span>
          <div className="flex-1">
            <span className="text-sm font-semibold" style={{ color: "#6FAF82" }}>
              {show_activo}
            </span>
          </div>
          {minutos_para_headliner !== null && minutos_para_headliner > 0 && (
            <span className="text-sm font-mono" style={{ color: "#D48B3A" }}>
              Headliner em {minutos_para_headliner} min
            </span>
          )}
        </div>
      )}
    </div>
  );
}
