"use client";

import type { ClusterData, SectionKey } from "@/types";
import { getStatusColor } from "@/lib/colors";
import { getClusterMeta, isUnissex } from "@/lib/clusters";

interface ClusterDrawerProps {
  cluster: ClusterData | null;
  onClose: () => void;
}

function SectionDetail({
  label,
  section,
}: {
  label: string;
  section: NonNullable<ClusterData["secoes"][SectionKey]>;
}) {
  const colors = getStatusColor(section.status);
  return (
    <div
      style={{
        backgroundColor: "#0f1117",
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
      }}
      className="p-3"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-bold" style={{ color: "#e2e8f0" }}>
          {label}
        </span>
        <span
          className="text-xs px-2 py-0.5 rounded font-semibold"
          style={{ backgroundColor: colors.bg, color: colors.text }}
        >
          {colors.label}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span style={{ color: "#94a3b8" }}>Ocupação</span>
          <p className="font-mono font-bold" style={{ color: "#e2e8f0" }}>
            {section.ocupacao_pct.toFixed(0)}%{" "}
            <span style={{ color: "#94a3b8" }}>
              ({section.ocupacao_absoluta} pessoas)
            </span>
          </p>
        </div>
        <div>
          <span style={{ color: "#94a3b8" }}>Fila</span>
          <p className="font-mono font-bold" style={{ color: "#e2e8f0" }}>
            {section.fila_actual}{" "}
            <span style={{ color: "#94a3b8" }}>
              (~{section.tempo_espera_min.toFixed(0)}min)
            </span>
          </p>
        </div>
        <div>
          <span style={{ color: "#94a3b8" }}>Entrada</span>
          <p className="font-mono font-bold" style={{ color: "#6FAF82" }}>
            {section.fluxo_entrada_pmin.toFixed(1)}/min
          </p>
        </div>
        <div>
          <span style={{ color: "#94a3b8" }}>Saída</span>
          <p className="font-mono font-bold" style={{ color: "#D48B3A" }}>
            {section.fluxo_saida_pmin.toFixed(1)}/min
          </p>
        </div>
        <div className="col-span-2">
          <span style={{ color: "#94a3b8" }}>Sensores</span>
          <p style={{ color: "#e2e8f0" }}>
            {section.fontes_activas.join(" · ")}{" "}
            <span style={{ color: "#94a3b8" }}>
              (conf. {section.confianca_pct.toFixed(0)}%)
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ClusterDrawer({ cluster, onClose }: ClusterDrawerProps) {
  if (!cluster) return null;

  const meta = getClusterMeta(cluster.cluster_id);
  const unissex = isUnissex(cluster.cluster_id);

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40"
        style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 bottom-0 z-50 overflow-y-auto w-full max-w-sm"
        style={{
          backgroundColor: "#1a1f2e",
          borderLeft: "1px solid #2d3348",
        }}
      >
        <div className="p-4">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold" style={{ color: "#e2e8f0" }}>
                {cluster.cluster_id}
              </h2>
              <p className="text-sm" style={{ color: "#94a3b8" }}>
                {cluster.nome || meta.nome}
              </p>
              <p className="text-xs mt-1" style={{ color: "#4b5563" }}>
                {cluster.dist_entrada_m}m da entrada
                {cluster.entry_only && (
                  <span
                    className="ml-2 px-1.5 py-0.5 rounded text-xs"
                    style={{ backgroundColor: "#D48B3A22", color: "#D48B3A" }}
                  >
                    ENTRY ONLY
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded"
              style={{
                backgroundColor: "#2d3348",
                color: "#94a3b8",
              }}
            >
              ✕
            </button>
          </div>

          {/* Tipo badge */}
          <div className="mb-4">
            <span
              className="text-xs px-2 py-0.5 rounded"
              style={{
                backgroundColor: unissex ? "#4A7C5922" : "#2d3348",
                color: unissex ? "#6FAF82" : "#94a3b8",
                border: `1px solid ${unissex ? "#4A7C59" : "#3d4558"}`,
              }}
            >
              {unissex ? "Unissex" : "Misto (M + F)"}
            </span>
          </div>

          {/* Sections */}
          <div className="flex flex-col gap-3 mb-4">
            {unissex && cluster.secoes.U && (
              <SectionDetail label="Unissex" section={cluster.secoes.U} />
            )}
            {!unissex && cluster.secoes.M && (
              <SectionDetail label="Masculino" section={cluster.secoes.M} />
            )}
            {!unissex && cluster.secoes.F && (
              <SectionDetail label="Feminino" section={cluster.secoes.F} />
            )}
          </div>

          {/* Active alerts */}
          {cluster.alertas.filter((a) => !a.resolvido).length > 0 && (
            <div>
              <h3
                className="text-xs font-semibold mb-2 uppercase tracking-wide"
                style={{ color: "#94a3b8" }}
              >
                Alertas Activos
              </h3>
              <div className="flex flex-col gap-2">
                {cluster.alertas
                  .filter((a) => !a.resolvido)
                  .map((alert) => (
                    <div
                      key={alert.id}
                      className="text-xs p-2 rounded"
                      style={{
                        backgroundColor:
                          alert.severidade === "CRITICO"
                            ? "#C25A1A22"
                            : "#D48B3A22",
                        border: `1px solid ${
                          alert.severidade === "CRITICO"
                            ? "#C25A1A"
                            : "#D48B3A"
                        }`,
                        color: "#e2e8f0",
                      }}
                    >
                      <span
                        className="font-bold"
                        style={{
                          color:
                            alert.severidade === "CRITICO"
                              ? "#C25A1A"
                              : "#D48B3A",
                        }}
                      >
                        [{alert.severidade}]
                      </span>{" "}
                      {alert.mensagem}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
