"use client";

import { useState } from "react";
import type { ClusterData, SectionKey } from "@/types";
import { getStatusColor } from "@/lib/colors";
import { getClusterMeta, isUnissex } from "@/lib/clusters";
import GaugeCircle from "./GaugeCircle";
import ClusterDrawer from "@/components/twin/ClusterDrawer";

interface ClusterCardProps {
  cluster: ClusterData;
}

function SectionRow({
  section,
}: {
  section: NonNullable<ClusterData["secoes"][SectionKey]>;
}) {
  return (
    <div className="grid grid-cols-3 text-xs gap-1 mt-1">
      <div>
        <span style={{ color: "#94a3b8" }}>Fila</span>
        <p className="font-mono" style={{ color: "#e2e8f0" }}>
          {section.fila_actual} (~{section.tempo_espera_min.toFixed(0)}min)
        </p>
      </div>
      <div>
        <span style={{ color: "#94a3b8" }}>Entrada</span>
        <p className="font-mono" style={{ color: "#6FAF82" }}>
          {section.fluxo_entrada_pmin.toFixed(1)}/min
        </p>
      </div>
      <div>
        <span style={{ color: "#94a3b8" }}>Saída</span>
        <p className="font-mono" style={{ color: "#D48B3A" }}>
          {section.fluxo_saida_pmin.toFixed(1)}/min
        </p>
      </div>
    </div>
  );
}

export default function ClusterCard({ cluster }: ClusterCardProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const meta = getClusterMeta(cluster.cluster_id);
  const unissex = isUnissex(cluster.cluster_id);

  // Determine worst status for card border
  const sections = Object.values(cluster.secoes).filter(Boolean);
  const order: Record<string, number> = {
    critico: 0, cheio: 1, moderado: 2, livre: 3, offline: 4,
  };
  const worstStatus =
    sections.sort(
      (a, b) =>
        (order[a?.status ?? "offline"] ?? 5) -
        (order[b?.status ?? "offline"] ?? 5)
    )[0]?.status ?? "offline";
  const colors = getStatusColor(worstStatus);

  const hasAlerts = cluster.alertas.filter((a) => !a.resolvido).length > 0;

  return (
    <>
      <div
        onClick={() => setDrawerOpen(true)}
        style={{
          backgroundColor: "#1a1f2e",
          border: `1px solid ${worstStatus === "critico" ? "#C25A1A" : "#2d3348"}`,
          borderRadius: 10,
          cursor: "pointer",
          transition: "border-color 0.2s",
        }}
        className="p-4 hover:brightness-110"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold" style={{ color: "#e2e8f0" }}>
                {cluster.cluster_id}
              </h3>
              {hasAlerts && (
                <span
                  className="text-xs px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: "#C25A1A22", color: "#C25A1A" }}
                >
                  ⚠
                </span>
              )}
            </div>
            <p className="text-xs" style={{ color: "#94a3b8" }}>
              {cluster.nome || meta.nome}
            </p>
            <p className="text-xs" style={{ color: "#4b5563" }}>
              {cluster.dist_entrada_m}m entrada
              {cluster.entry_only && (
                <span className="ml-1" style={{ color: "#D48B3A" }}>
                  · ENTRY ONLY
                </span>
              )}
            </p>
          </div>
          <span
            className="text-xs px-2 py-1 rounded font-semibold shrink-0"
            style={{ backgroundColor: colors.bg, color: colors.text }}
          >
            {colors.label}
          </span>
        </div>

        {/* Gauges */}
        {unissex ? (
          <div className="flex justify-center py-2">
            {cluster.secoes.U && (
              <GaugeCircle pct={cluster.secoes.U.ocupacao_pct} label="U" size={90} />
            )}
          </div>
        ) : (
          <div className="flex justify-around py-2">
            {cluster.secoes.M && (
              <GaugeCircle pct={cluster.secoes.M.ocupacao_pct} label="M" size={90} />
            )}
            {cluster.secoes.F && (
              <GaugeCircle pct={cluster.secoes.F.ocupacao_pct} label="F" size={90} />
            )}
          </div>
        )}

        {/* Section detail rows */}
        <div
          style={{ borderTop: "1px solid #2d3348" }}
          className="pt-2 mt-2"
        >
          {unissex && cluster.secoes.U && (
            <SectionRow section={cluster.secoes.U} />
          )}
          {!unissex && (
            <>
              {cluster.secoes.M && (
                <>
                  <p className="text-xs font-semibold" style={{ color: "#60a5fa" }}>
                    Masculino
                  </p>
                  <SectionRow section={cluster.secoes.M} />
                </>
              )}
              {cluster.secoes.F && (
                <>
                  <p className="text-xs font-semibold mt-2" style={{ color: "#c084fc" }}>
                    Feminino
                  </p>
                  <SectionRow section={cluster.secoes.F} />
                </>
              )}
            </>
          )}
        </div>

        {/* Sensor confidence */}
        <div className="mt-2 flex flex-wrap gap-1">
          {sections[0]?.fontes_activas.map((fonte) => (
            <span
              key={fonte}
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ backgroundColor: "#2d3348", color: "#6FAF82" }}
            >
              {fonte}
            </span>
          ))}
          {sections[0] && (
            <span
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ backgroundColor: "#2d3348", color: "#94a3b8" }}
            >
              conf. {sections[0].confianca_pct.toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      <ClusterDrawer
        cluster={drawerOpen ? cluster : null}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}
