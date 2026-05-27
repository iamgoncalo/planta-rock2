"use client";

import { getOccupancyColor } from "@/lib/colors";

interface GaugeCircleProps {
  pct: number;
  label: "M" | "F" | "U";
  size?: number;
}

export default function GaugeCircle({ pct, label, size = 80 }: GaugeCircleProps) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedPct = Math.min(100, Math.max(0, pct));
  const dashOffset = circumference * (1 - clampedPct / 100);
  const color = getOccupancyColor(clampedPct);
  const cx = size / 2;
  const cy = size / 2;

  const labelColors: Record<string, { bg: string; text: string }> = {
    M: { bg: "#1e3a5f", text: "#60a5fa" },
    F: { bg: "#3d1a3d", text: "#c084fc" },
    U: { bg: "#1a3d28", text: "#6FAF82" },
  };
  const lc = labelColors[label] ?? { bg: "#2d3348", text: "#e2e8f0" };

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} aria-label={`${label}: ${pct}%`}>
        {/* Background ring */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="#2d3348"
          strokeWidth="8"
        />
        {/* Arc */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: "stroke-dashoffset 0.5s ease-in-out, stroke 0.3s ease" }}
        />
        {/* Center text */}
        <text
          x={cx}
          y={cy + 1}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={size < 70 ? "11" : "13"}
          fontWeight="bold"
          fill="#e2e8f0"
          fontFamily="monospace"
        >
          {clampedPct.toFixed(0)}%
        </text>
      </svg>
      <span
        className="text-xs font-bold px-2 py-0.5 rounded"
        style={{ backgroundColor: lc.bg, color: lc.text }}
      >
        {label === "U" ? "Unissex" : label === "M" ? "Masc." : "Fem."}
      </span>
    </div>
  );
}
