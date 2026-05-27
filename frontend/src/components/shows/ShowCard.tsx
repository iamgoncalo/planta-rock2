"use client";

import type { Show } from "@/types";
import { STAGE_LABELS } from "@/lib/shows";

interface ShowCardProps {
  show: Show;
  isActive?: boolean;
  onClick?: (show: Show) => void;
}

export default function ShowCard({ show, isActive, onClick }: ShowCardProps) {
  return (
    <div
      onClick={() => onClick?.(show)}
      style={{
        backgroundColor: isActive ? "#1e2a1e" : "#1a1f2e",
        border: `1px solid ${
          isActive ? "#4A7C59" : show.headliner ? "#D48B3A" : "#2d3348"
        }`,
        borderRadius: 8,
        cursor: onClick ? "pointer" : "default",
        transition: "border-color 0.2s, background-color 0.2s",
      }}
      className="p-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs" style={{ color: "#94a3b8" }}>
              {show.hora_inicio}–{show.hora_fim}
            </span>
            <span
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ backgroundColor: "#2d3348", color: "#94a3b8" }}
            >
              {STAGE_LABELS[show.palco] ?? show.palco}
            </span>
            {isActive && (
              <span
                className="text-xs px-1.5 py-0.5 rounded font-semibold"
                style={{ backgroundColor: "#4A7C5944", color: "#6FAF82" }}
              >
                AO VIVO
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1">
            {show.headliner && (
              <span style={{ color: "#D48B3A" }}>★</span>
            )}
            <h4
              className="font-bold text-sm"
              style={{ color: "#e2e8f0" }}
            >
              {show.artista}
            </h4>
          </div>
          <p className="text-xs mt-0.5" style={{ color: "#94a3b8" }}>
            {show.genero}
          </p>
        </div>

        {/* Surge indicator */}
        {show.surge_esperado_30min_apos && (
          <div
            className="shrink-0 text-xs px-2 py-1 rounded text-center"
            style={{
              backgroundColor: "#D48B3A22",
              border: "1px solid #D48B3A44",
              color: "#D48B3A",
            }}
          >
            <div>⚡</div>
            <div className="text-xs">surge</div>
          </div>
        )}
      </div>
    </div>
  );
}
