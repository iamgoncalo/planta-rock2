"use client";

import { useState } from "react";
import type { Show } from "@/types";
import { STAGE_LABELS } from "@/lib/shows";
import ShowCard from "./ShowCard";

interface ProgrammeProps {
  shows: Show[];
  currentShowId?: string | null;
}

function StageSection({ stage, shows, currentShowId, onSelect }: {
  stage: string;
  shows: Show[];
  currentShowId?: string | null;
  onSelect: (show: Show) => void;
}) {
  return (
    <div className="mb-6">
      <h3
        className="text-xs font-semibold uppercase tracking-wider mb-2 px-1"
        style={{ color: "#94a3b8" }}
      >
        {STAGE_LABELS[stage] ?? stage}
      </h3>
      <div className="flex flex-col gap-2">
        {shows.map((show) => (
          <ShowCard
            key={show.id}
            show={show}
            isActive={show.id === currentShowId}
            onClick={onSelect}
          />
        ))}
      </div>
    </div>
  );
}

export default function Programme({ shows, currentShowId }: ProgrammeProps) {
  const [selectedShow, setSelectedShow] = useState<Show | null>(null);

  // Group by stage
  const byStage = shows.reduce<Record<string, Show[]>>((acc, show) => {
    if (!acc[show.palco]) acc[show.palco] = [];
    acc[show.palco].push(show);
    return acc;
  }, {});

  const stageOrder = ["PM", "PMV", "PSB", "PBP"];

  return (
    <div className="flex flex-col md:flex-row gap-4">
      {/* Programme list */}
      <div className="flex-1">
        {shows.length === 0 && (
          <div
            className="py-12 text-center text-sm"
            style={{ color: "#4b5563" }}
          >
            Sem shows para este dia
          </div>
        )}
        {stageOrder
          .filter((s) => byStage[s]?.length > 0)
          .map((stage) => (
            <StageSection
              key={stage}
              stage={stage}
              shows={byStage[stage]}
              currentShowId={currentShowId}
              onSelect={setSelectedShow}
            />
          ))}
      </div>

      {/* Show detail panel */}
      {selectedShow && (
        <div
          className="w-full md:w-80 shrink-0"
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            borderRadius: 10,
            padding: 16,
            height: "fit-content",
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <h3 className="font-bold text-lg" style={{ color: "#e2e8f0" }}>
              {selectedShow.artista}
            </h3>
            <button
              onClick={() => setSelectedShow(null)}
              className="p-1 rounded"
              style={{ backgroundColor: "#2d3348", color: "#94a3b8" }}
            >
              ✕
            </button>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex gap-2">
              <span style={{ color: "#94a3b8" }}>Palco:</span>
              <span style={{ color: "#e2e8f0" }}>
                {STAGE_LABELS[selectedShow.palco]}
              </span>
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#94a3b8" }}>Hora:</span>
              <span className="font-mono" style={{ color: "#e2e8f0" }}>
                {selectedShow.hora_inicio} → {selectedShow.hora_fim}
              </span>
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#94a3b8" }}>Género:</span>
              <span style={{ color: "#e2e8f0" }}>{selectedShow.genero}</span>
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#94a3b8" }}>Headliner:</span>
              <span style={{ color: selectedShow.headliner ? "#D48B3A" : "#6B7280" }}>
                {selectedShow.headliner ? "★ Sim" : "Não"}
              </span>
            </div>
            {selectedShow.surge_esperado_30min_apos && (
              <div
                className="mt-2 p-2 rounded text-xs"
                style={{
                  backgroundColor: "#D48B3A22",
                  border: "1px solid #D48B3A44",
                  color: "#D48B3A",
                }}
              >
                ⚡ Surge esperado nos 30 minutos após o show
              </div>
            )}
            {selectedShow.clusters_afectados.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-semibold mb-1" style={{ color: "#94a3b8" }}>
                  Clusters afectados:
                </p>
                <div className="flex flex-wrap gap-1">
                  {selectedShow.clusters_afectados.map((id) => (
                    <span
                      key={id}
                      className="text-xs px-2 py-0.5 rounded"
                      style={{ backgroundColor: "#2d3348", color: "#e2e8f0" }}
                    >
                      {id}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
