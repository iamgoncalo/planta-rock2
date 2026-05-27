"use client";

import { useState, useEffect } from "react";
import { fetchClusters } from "@/lib/api";
import { getClusterMeta } from "@/lib/clusters";
import { getStatusColor } from "@/lib/colors";
import type { ClusterData } from "@/types";

function getAvgOcc(c: ClusterData): number {
  const secs = Object.values(c.secoes).filter(Boolean);
  if (!secs.length) return 0;
  return secs.reduce((s, sec) => s + (sec?.ocupacao_pct ?? 0), 0) / secs.length;
}

function getAvgQueue(c: ClusterData): number {
  const secs = Object.values(c.secoes).filter(Boolean);
  if (!secs.length) return 0;
  return secs.reduce((s, sec) => s + (sec?.fila_actual ?? 0), 0);
}

function getAvgWait(c: ClusterData): number {
  const secs = Object.values(c.secoes).filter(Boolean);
  if (!secs.length) return 0;
  return secs.reduce((s, sec) => s + (sec?.tempo_espera_min ?? 0), 0) / secs.length;
}

function getWorstStatus(c: ClusterData): string {
  const order: Record<string, number> = {
    critico: 0, cheio: 1, moderado: 2, livre: 3, offline: 4,
  };
  const secs = Object.values(c.secoes).filter(Boolean);
  return (
    secs.sort(
      (a, b) =>
        (order[a?.status ?? "offline"] ?? 5) -
        (order[b?.status ?? "offline"] ?? 5)
    )[0]?.status ?? "offline"
  );
}

export default function AppPage() {
  const [clusters, setClusters] = useState<ClusterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchClusters();
        setClusters(data.clusters);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro de ligação");
      } finally {
        setLoading(false);
      }
    }
    load();
    const t = setInterval(load, 30000); // refresh every 30s
    return () => clearInterval(t);
  }, []);

  // Sort by occupancy ascending, exclude entry_only for suggestions
  const available = clusters
    .filter((c) => !c.entry_only)
    .sort((a, b) => getAvgOcc(a) - getAvgOcc(b));

  const best = available[0];
  const avoid = clusters.filter((c) => {
    const s = getWorstStatus(c);
    return s === "critico" || s === "cheio";
  });

  if (loading) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center gap-4"
        style={{ backgroundColor: "#0f1117", color: "#e2e8f0" }}
      >
        <div
          className="w-10 h-10 rounded-full border-2 animate-spin"
          style={{ borderColor: "#4A7C59", borderTopColor: "transparent" }}
        />
        <p style={{ color: "#94a3b8" }}>A carregar...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center gap-4 px-4"
        style={{ backgroundColor: "#0f1117", color: "#e2e8f0" }}
      >
        <p className="text-4xl">📵</p>
        <h2 className="text-lg font-bold">Serviço indisponível</h2>
        <p className="text-sm text-center" style={{ color: "#94a3b8" }}>
          Não foi possível ligar ao servidor. Tenta novamente em breve.
        </p>
      </div>
    );
  }

  return (
    <div
      className="max-w-sm mx-auto py-6 px-4"
      style={{ color: "#e2e8f0" }}
    >
      {/* Header */}
      <div className="text-center mb-6">
        <div
          className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center text-xl font-bold"
          style={{ backgroundColor: "#4A7C59" }}
        >
          WC
        </div>
        <h1 className="text-xl font-bold">Encontra a tua casa de banho</h1>
        <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
          Rock in Rio Lisboa 2026
        </p>
      </div>

      {/* Best recommendation */}
      {best && (
        <div
          className="mb-4 p-4 rounded-xl"
          style={{
            backgroundColor: "#1e2a1e",
            border: "2px solid #4A7C59",
          }}
        >
          <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "#6FAF82" }}>
            Melhor opção agora
          </p>
          <h2 className="text-lg font-bold mb-1" style={{ color: "#e2e8f0" }}>
            {best.cluster_id}
          </h2>
          <p className="text-sm mb-3" style={{ color: "#94a3b8" }}>
            {best.nome || getClusterMeta(best.cluster_id).nome}
          </p>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div
              className="rounded-lg p-2"
              style={{ backgroundColor: "#0f1117" }}
            >
              <p className="text-lg font-bold font-mono" style={{ color: "#6FAF82" }}>
                {getAvgOcc(best).toFixed(0)}%
              </p>
              <p className="text-xs" style={{ color: "#94a3b8" }}>
                Ocupação
              </p>
            </div>
            <div
              className="rounded-lg p-2"
              style={{ backgroundColor: "#0f1117" }}
            >
              <p className="text-lg font-bold font-mono" style={{ color: "#e2e8f0" }}>
                {getAvgQueue(best)}
              </p>
              <p className="text-xs" style={{ color: "#94a3b8" }}>
                Fila
              </p>
            </div>
            <div
              className="rounded-lg p-2"
              style={{ backgroundColor: "#0f1117" }}
            >
              <p className="text-lg font-bold font-mono" style={{ color: "#e2e8f0" }}>
                {best.dist_entrada_m}m
              </p>
              <p className="text-xs" style={{ color: "#94a3b8" }}>
                Distância
              </p>
            </div>
          </div>

          {getAvgWait(best) > 0 && (
            <p className="text-xs mt-2 text-center" style={{ color: "#94a3b8" }}>
              Espera estimada: ~{getAvgWait(best).toFixed(0)} min
            </p>
          )}

          {/* Type badge - correctly handles unisex */}
          <div className="mt-3 flex justify-center">
            <span
              className="text-xs px-2 py-1 rounded"
              style={{
                backgroundColor:
                  best.tipo === "unissex" ? "#4A7C5922" : "#2d3348",
                color:
                  best.tipo === "unissex" ? "#6FAF82" : "#94a3b8",
              }}
            >
              {best.tipo === "unissex" ? "Unissex" : "Masculino + Feminino"}
            </span>
          </div>
        </div>
      )}

      {/* Avoid list */}
      {avoid.length > 0 && (
        <div
          className="mb-4 p-3 rounded-xl"
          style={{
            backgroundColor: "#1a1510",
            border: "1px solid #C25A1A44",
          }}
        >
          <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "#C25A1A" }}>
            Evitar agora
          </p>
          {avoid.map((c) => (
            <div key={c.cluster_id} className="flex justify-between text-sm py-1">
              <span style={{ color: "#e2e8f0" }}>
                {c.cluster_id} — {c.nome}
              </span>
              <span style={{ color: "#C25A1A" }}>
                {getAvgOcc(c).toFixed(0)}% cheio
              </span>
            </div>
          ))}
        </div>
      )}

      {/* All clusters list */}
      <div
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          borderRadius: 12,
        }}
      >
        <button
          onClick={() => setShowAll(!showAll)}
          className="w-full px-4 py-3 flex items-center justify-between text-sm font-medium"
          style={{ color: "#e2e8f0" }}
        >
          <span>Ver todas as casas de banho</span>
          <span style={{ color: "#94a3b8" }}>{showAll ? "▲" : "▼"}</span>
        </button>

        {showAll && (
          <div style={{ borderTop: "1px solid #2d3348" }}>
            {clusters
              .sort((a, b) => getAvgOcc(a) - getAvgOcc(b))
              .map((c, i, arr) => {
                const occ = getAvgOcc(c);
                const status = getWorstStatus(c);
                const colors = getStatusColor(status as Parameters<typeof getStatusColor>[0]);
                const meta = getClusterMeta(c.cluster_id);

                return (
                  <div
                    key={c.cluster_id}
                    className="px-4 py-3 flex items-center justify-between"
                    style={{
                      borderBottom:
                        i < arr.length - 1 ? "1px solid #1e2330" : "none",
                    }}
                  >
                    <div>
                      <p className="font-bold text-sm" style={{ color: "#e2e8f0" }}>
                        {c.cluster_id}
                      </p>
                      <p className="text-xs" style={{ color: "#94a3b8" }}>
                        {c.nome || meta.nome} · {c.dist_entrada_m}m
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "#94a3b8" }}>
                        {c.tipo === "unissex" ? "Unissex" : "M + F"}
                        {c.entry_only && (
                          <span style={{ color: "#D48B3A" }}>
                            {" "}
                            · Só entrada
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="text-right">
                      <p
                        className="font-bold font-mono"
                        style={{ color: colors.bg }}
                      >
                        {occ.toFixed(0)}%
                      </p>
                      <p className="text-xs" style={{ color: colors.bg }}>
                        {colors.label}
                      </p>
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>

      {/* Refresh note */}
      <p className="text-xs text-center mt-4" style={{ color: "#2d3348" }}>
        Actualiza automaticamente a cada 30 segundos
      </p>
    </div>
  );
}
