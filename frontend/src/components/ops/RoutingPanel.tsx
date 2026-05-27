"use client";

import type { RoutingRecommendation } from "@/types";

interface RoutingPanelProps {
  recommendations: RoutingRecommendation[];
}

export default function RoutingPanel({ recommendations }: RoutingPanelProps) {
  return (
    <div>
      <h2 className="font-bold text-sm mb-3" style={{ color: "#e2e8f0" }}>
        Recomendações de Routing
      </h2>

      {recommendations.length === 0 && (
        <div
          className="py-8 text-center text-sm rounded-lg"
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            color: "#4b5563",
          }}
        >
          Sem recomendações activas
        </div>
      )}

      <div className="flex flex-col gap-2">
        {recommendations.map((rec, i) => (
          <div
            key={i}
            className="p-3 rounded-lg"
            style={{
              backgroundColor: "#1a1f2e",
              border: "1px solid #2d3348",
            }}
          >
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <span
                className="font-bold px-2 py-0.5 rounded"
                style={{ backgroundColor: "#C25A1A22", color: "#C25A1A" }}
              >
                {rec.from_cluster}
              </span>
              <span style={{ color: "#94a3b8" }}>→</span>
              <span
                className="font-bold px-2 py-0.5 rounded"
                style={{ backgroundColor: "#4A7C5922", color: "#6FAF82" }}
              >
                {rec.to_cluster}
              </span>
              <span
                className="text-xs px-1.5 py-0.5 rounded"
                style={{ backgroundColor: "#2d3348", color: "#94a3b8" }}
              >
                {rec.distance_m}m
              </span>
            </div>
            <p className="text-xs mt-1.5" style={{ color: "#94a3b8" }}>
              {rec.reason}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
