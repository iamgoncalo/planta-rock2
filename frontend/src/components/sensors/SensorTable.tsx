"use client";

import { useState } from "react";
import type { ClusterData } from "@/types";
import { getClusterMeta } from "@/lib/clusters";

function SensorDot({ active }: { active: boolean }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        backgroundColor: active ? "#6FAF82" : "#6B7280",
        marginRight: 4,
      }}
    />
  );
}

function ConfBar({ pct }: { pct: number }) {
  const color = pct >= 80 ? "#6FAF82" : pct >= 50 ? "#D48B3A" : "#C25A1A";
  return (
    <div className="flex items-center gap-1">
      <div
        style={{
          width: 40,
          height: 6,
          backgroundColor: "#2d3348",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            backgroundColor: color,
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <span className="text-xs font-mono" style={{ color }}>
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

export default function SensorTable({ clusters }: { clusters: ClusterData[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Summary counts
  const irOnline = clusters.reduce((sum, c) => {
    const sections = Object.values(c.secoes).filter(Boolean);
    return (
      sum +
      sections.filter((s) => s?.fontes_activas.includes("IR")).length * 2 // entry + exit
    );
  }, 0);

  const lilyGoOnline = clusters.filter((c) => {
    const sections = Object.values(c.secoes).filter(Boolean);
    return sections.some((s) => s?.fontes_activas.includes("WiFi"));
  }).length;

  const cameraOnline = clusters.filter((c) => {
    const sections = Object.values(c.secoes).filter(Boolean);
    return sections.some((s) => s?.fontes_activas.includes("Camera"));
  }).length;

  return (
    <div>
      {/* Summary header */}
      <div
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          borderRadius: 8,
        }}
        className="p-3 mb-4 flex flex-wrap gap-4 text-sm"
      >
        <span>
          <SensorDot active={irOnline > 0} />
          <span style={{ color: "#e2e8f0" }}>{irOnline}</span>
          <span style={{ color: "#94a3b8" }}>/24 sensores IR</span>
        </span>
        <span>
          <SensorDot active={lilyGoOnline > 0} />
          <span style={{ color: "#e2e8f0" }}>{lilyGoOnline}</span>
          <span style={{ color: "#94a3b8" }}>/8 LilyGos</span>
        </span>
        <span>
          <SensorDot active={cameraOnline > 0} />
          <span style={{ color: "#e2e8f0" }}>{cameraOnline}</span>
          <span style={{ color: "#94a3b8" }}>/8 câmaras</span>
        </span>
      </div>

      {/* Table */}
      <div
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          borderRadius: 8,
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          className="grid text-xs font-semibold uppercase tracking-wide px-4 py-2"
          style={{
            color: "#94a3b8",
            backgroundColor: "#13161f",
            borderBottom: "1px solid #2d3348",
            gridTemplateColumns: "120px 1fr 1fr 1fr 1fr 80px",
          }}
        >
          <span>Cluster</span>
          <span>LilyGo</span>
          <span>IR Entrada</span>
          <span>IR Saída</span>
          <span>Câmara</span>
          <span>Confiança</span>
        </div>

        {clusters.map((c, idx) => {
          const meta = getClusterMeta(c.cluster_id);
          const sections = Object.values(c.secoes).filter(Boolean);
          const allFontes = new Set(sections.flatMap((s) => s?.fontes_activas ?? []));
          const avgConf =
            sections.length > 0
              ? sections.reduce((sum, s) => sum + (s?.confianca_pct ?? 0), 0) /
                sections.length
              : 0;

          const hasWifi = allFontes.has("WiFi");
          const hasIR = allFontes.has("IR");
          const hasCamera = allFontes.has("Camera");

          const isExpanded = expandedId === c.cluster_id;

          return (
            <div key={c.cluster_id}>
              <div
                className="grid px-4 py-3 text-sm items-center cursor-pointer hover:brightness-110"
                style={{
                  gridTemplateColumns: "120px 1fr 1fr 1fr 1fr 80px",
                  borderBottom:
                    idx < clusters.length - 1 || isExpanded
                      ? "1px solid #2d3348"
                      : "none",
                  backgroundColor: isExpanded ? "#1e2440" : "transparent",
                }}
                onClick={() =>
                  setExpandedId(isExpanded ? null : c.cluster_id)
                }
              >
                <div>
                  <p className="font-bold" style={{ color: "#e2e8f0" }}>
                    {c.cluster_id}
                  </p>
                  <p className="text-xs" style={{ color: "#94a3b8" }}>
                    {meta.nome.split("—")[0].trim()}
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  <SensorDot active={hasWifi} />
                  <span
                    className="text-xs"
                    style={{ color: hasWifi ? "#6FAF82" : "#6B7280" }}
                  >
                    {hasWifi ? "Online" : "Offline"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <SensorDot active={hasIR} />
                  <span
                    className="text-xs font-mono"
                    style={{ color: hasIR ? "#6FAF82" : "#6B7280" }}
                  >
                    {hasIR
                      ? `${sections
                          .reduce((s, sec) => s + (sec?.fluxo_entrada_pmin ?? 0), 0)
                          .toFixed(1)}/min`
                      : "—"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <SensorDot active={hasIR} />
                  <span
                    className="text-xs font-mono"
                    style={{ color: hasIR ? "#D48B3A" : "#6B7280" }}
                  >
                    {hasIR
                      ? `${sections
                          .reduce((s, sec) => s + (sec?.fluxo_saida_pmin ?? 0), 0)
                          .toFixed(1)}/min`
                      : "—"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <SensorDot active={hasCamera} />
                  <span
                    className="text-xs"
                    style={{ color: hasCamera ? "#6FAF82" : "#6B7280" }}
                  >
                    {hasCamera ? "Activa" : "Offline"}
                  </span>
                </div>
                <ConfBar pct={avgConf} />
              </div>

              {/* Expanded detail */}
              {isExpanded && (
                <div
                  className="px-4 py-3"
                  style={{
                    backgroundColor: "#0f1117",
                    borderBottom:
                      idx < clusters.length - 1 ? "1px solid #2d3348" : "none",
                  }}
                >
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {Object.entries(c.secoes).map(([key, sec]) => {
                      if (!sec) return null;
                      return (
                        <div
                          key={key}
                          style={{
                            backgroundColor: "#1a1f2e",
                            borderRadius: 6,
                            border: "1px solid #2d3348",
                          }}
                          className="p-2 text-xs"
                        >
                          <p
                            className="font-bold mb-1"
                            style={{ color: "#e2e8f0" }}
                          >
                            Secção {key === "U" ? "Unissex" : key}
                          </p>
                          <p style={{ color: "#94a3b8" }}>
                            Pessoas: {sec.ocupacao_absoluta}
                          </p>
                          <p style={{ color: "#94a3b8" }}>
                            Fluxo entrada: {sec.fluxo_entrada_pmin.toFixed(1)}/min
                          </p>
                          <p style={{ color: "#94a3b8" }}>
                            Fluxo saída: {sec.fluxo_saida_pmin.toFixed(1)}/min
                          </p>
                          <p style={{ color: "#94a3b8" }}>
                            Fontes: {sec.fontes_activas.join(", ")}
                          </p>
                          <p style={{ color: "#94a3b8" }}>
                            Confiança: {sec.confianca_pct.toFixed(0)}%
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
