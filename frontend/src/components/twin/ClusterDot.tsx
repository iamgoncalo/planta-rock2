"use client";

import type { ClusterData } from "@/types";
import { getStatusColor } from "@/lib/colors";

interface ClusterDotProps {
  cluster: ClusterData;
  x: number;
  y: number;
  onClick: (cluster: ClusterData) => void;
}

function getMainOccupancy(cluster: ClusterData): number {
  const sections = Object.values(cluster.secoes).filter(Boolean);
  if (sections.length === 0) return 0;
  const avg =
    sections.reduce((sum, s) => sum + (s?.ocupacao_pct ?? 0), 0) /
    sections.length;
  return Math.round(avg);
}

function getWorstStatus(cluster: ClusterData): ClusterData["secoes"][keyof ClusterData["secoes"]] {
  const sections = Object.values(cluster.secoes).filter(Boolean);
  const order: Record<string, number> = {
    critico: 0,
    cheio: 1,
    moderado: 2,
    livre: 3,
    offline: 4,
  };
  return sections.sort(
    (a, b) => (order[a?.status ?? "offline"] ?? 5) - (order[b?.status ?? "offline"] ?? 5)
  )[0];
}

export default function ClusterDot({ cluster, x, y, onClick }: ClusterDotProps) {
  const worstSection = getWorstStatus(cluster);
  const status = worstSection?.status ?? "offline";
  const colors = getStatusColor(status);
  const occupancy = getMainOccupancy(cluster);
  const isCritical = status === "critico";

  const r = 22;

  return (
    <g
      onClick={() => onClick(cluster)}
      style={{ cursor: "pointer" }}
      transform={`translate(${x}, ${y})`}
    >
      {/* Pulse ring for critical */}
      {isCritical && (
        <>
          <circle
            r={r + 8}
            fill="none"
            stroke="#C25A1A"
            strokeWidth="2"
            opacity="0.3"
          >
            <animate
              attributeName="r"
              values={`${r + 4};${r + 14};${r + 4}`}
              dur="2s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="0.5;0;0.5"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
        </>
      )}

      {/* Main circle */}
      <circle
        r={r}
        fill={colors.bg}
        stroke={colors.border}
        strokeWidth="2"
      />

      {/* Percentage text */}
      <text
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="10"
        fontWeight="bold"
        fill={colors.text}
        y="-3"
      >
        {occupancy}%
      </text>

      {/* Cluster ID */}
      <text
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="8"
        fill={colors.text}
        opacity="0.8"
        y="8"
      >
        {cluster.cluster_id}
      </text>
    </g>
  );
}
