import type { ClusterStatus } from "@/types";

// NO RED EVER — critical color is #C25A1A (burnt orange)
export const STATUS_COLORS: Record<
  ClusterStatus,
  { bg: string; text: string; label: string; border: string }
> = {
  livre: { bg: "#6FAF82", text: "#1a3d28", label: "Livre", border: "#4A7C59" },
  moderado: {
    bg: "#D48B3A",
    text: "#fff",
    label: "Moderado",
    border: "#b5712a",
  },
  cheio: { bg: "#D48B3A", text: "#fff", label: "Cheio", border: "#b5712a" },
  critico: {
    bg: "#C25A1A",
    text: "#fff",
    label: "Crítico",
    border: "#a04816",
  },
  offline: {
    bg: "#6B7280",
    text: "#fff",
    label: "Offline",
    border: "#4b5563",
  },
};

export function getStatusColor(status: ClusterStatus) {
  return STATUS_COLORS[status] ?? STATUS_COLORS.offline;
}

export function getOccupancyColor(pct: number): string {
  if (pct < 60) return "#6FAF82";
  if (pct < 85) return "#D48B3A";
  return "#C25A1A"; // never red
}

export function getSeverityStyle(
  severidade: "CRITICO" | "ALTO" | "MEDIO" | "INFO"
): { bg: string; text: string; border: string } {
  switch (severidade) {
    case "CRITICO":
      return { bg: "#C25A1A22", text: "#C25A1A", border: "#C25A1A" };
    case "ALTO":
      return { bg: "#D48B3A22", text: "#D48B3A", border: "#D48B3A" };
    case "MEDIO":
      return { bg: "#D4B43A22", text: "#D4B43A", border: "#D4B43A" };
    case "INFO":
      return { bg: "#4A7C5922", text: "#6FAF82", border: "#4A7C59" };
    default:
      return { bg: "#6B728022", text: "#94a3b8", border: "#6B7280" };
  }
}
