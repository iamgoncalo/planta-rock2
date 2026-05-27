"use client";

import { useState, useMemo } from "react";
import { useClusters } from "@/hooks/useClusters";
import ClusterCard from "@/components/occupation/ClusterCard";
import type { ClusterData } from "@/types";

type FilterKey = "todos" | "criticos" | "masculino" | "feminino" | "unissex";

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "todos", label: "Todos" },
  { key: "criticos", label: "Críticos" },
  { key: "masculino", label: "Masculino" },
  { key: "feminino", label: "Feminino" },
  { key: "unissex", label: "Unissex" },
];

function getAvgOccupancy(cluster: ClusterData): number {
  const sections = Object.values(cluster.secoes).filter(Boolean);
  if (sections.length === 0) return 0;
  return (
    sections.reduce((sum, s) => sum + (s?.ocupacao_pct ?? 0), 0) /
    sections.length
  );
}

function hasWorstStatus(cluster: ClusterData, status: string): boolean {
  return Object.values(cluster.secoes).some((s) => s?.status === status);
}

export default function OccupationPage() {
  const { clusters, loading, error } = useClusters();
  const [filter, setFilter] = useState<FilterKey>("todos");

  const filtered = useMemo(() => {
    let list = [...clusters];

    switch (filter) {
      case "criticos":
        list = list.filter((c) => hasWorstStatus(c, "critico"));
        break;
      case "masculino":
        list = list.filter((c) => c.tipo === "misto" && c.secoes.M);
        break;
      case "feminino":
        list = list.filter((c) => c.tipo === "misto" && c.secoes.F);
        break;
      case "unissex":
        list = list.filter((c) => c.tipo === "unissex");
        break;
    }

    // Sort by highest occupancy first
    list.sort((a, b) => getAvgOccupancy(b) - getAvgOccupancy(a));
    return list;
  }, [clusters, filter]);

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
          Ocupação
        </h1>
        <p className="text-sm" style={{ color: "#94a3b8" }}>
          Estado de ocupação por cluster e secção
        </p>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className="px-3 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              backgroundColor: filter === f.key ? "#4A7C59" : "#1a1f2e",
              color: filter === f.key ? "#fff" : "#94a3b8",
              border: `1px solid ${filter === f.key ? "#4A7C59" : "#2d3348"}`,
            }}
          >
            {f.label}
          </button>
        ))}
        <span
          className="ml-auto text-xs self-center"
          style={{ color: "#4b5563" }}
        >
          {filtered.length} clusters
        </span>
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
          Backend inacessível — {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div
              key={i}
              style={{
                backgroundColor: "#1a1f2e",
                borderRadius: 10,
                height: 220,
              }}
              className="animate-pulse"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((cluster) => (
            <ClusterCard key={cluster.cluster_id} cluster={cluster} />
          ))}
          {filtered.length === 0 && (
            <div
              className="col-span-2 py-16 text-center text-sm"
              style={{ color: "#4b5563" }}
            >
              Nenhum cluster encontrado para este filtro
            </div>
          )}
        </div>
      )}
    </div>
  );
}
