import type { ClusterMeta } from "@/types";

export const CLUSTER_META: Record<string, ClusterMeta> = {
  "WC-01": {
    nome: "V34 — Near P1",
    tipo: "misto",
    dist_entrada_m: 220,
    capacidadeM: 72,
    capacidadeF: 63,
  },
  "WC-02": {
    nome: "V35 — Female Dominant",
    tipo: "misto",
    dist_entrada_m: 180,
    capacidadeM: 54,
    capacidadeF: 72,
  },
  "WC-03": {
    nome: "S36 — Entrada Principal",
    tipo: "misto",
    dist_entrada_m: 33,
    capacidadeM: 54,
    capacidadeF: 48,
  },
  "WC-04": {
    nome: "S37 — Summit +20m",
    tipo: "misto",
    dist_entrada_m: 95,
    capacidadeM: 84,
    capacidadeF: 66,
  },
  "WC-05": {
    nome: "M38 — ENTRY ONLY",
    tipo: "unissex",
    dist_entrada_m: 45,
    capacidadeU: 133,
    entry_only: true,
  },
  "WC-06": {
    nome: "W39/S39 — Maior cluster",
    tipo: "unissex",
    dist_entrada_m: 267,
    capacidadeU: 208,
  },
  "WC-07": {
    nome: "M40 — Lockers",
    tipo: "misto",
    dist_entrada_m: 310,
    capacidadeM: 84,
    capacidadeF: 54,
  },
  "WC-08": {
    nome: "V41 — Produção",
    tipo: "misto",
    dist_entrada_m: 420,
    capacidadeM: 84,
    capacidadeF: 61,
  },
};

export const CLUSTER_IDS = Object.keys(CLUSTER_META);

// Approximate SVG positions from GPS coords
// Map bounds: lat 38.779-38.783, lon -9.097 to -9.092
// SVG viewport: 600x400
export const CLUSTER_SVG_POS: Record<string, { x: number; y: number }> = {
  "WC-01": { x: 520, y: 60 },
  "WC-02": { x: 490, y: 130 },
  "WC-03": { x: 400, y: 170 },
  "WC-04": { x: 450, y: 220 },
  "WC-05": { x: 310, y: 195 },
  "WC-06": { x: 160, y: 290 },
  "WC-07": { x: 230, y: 210 },
  "WC-08": { x: 100, y: 340 },
};

export function getClusterMeta(clusterId: string): ClusterMeta {
  return (
    CLUSTER_META[clusterId] ?? {
      nome: clusterId,
      tipo: "misto",
      dist_entrada_m: 0,
    }
  );
}

export function isUnissex(clusterId: string): boolean {
  return CLUSTER_META[clusterId]?.tipo === "unissex";
}
