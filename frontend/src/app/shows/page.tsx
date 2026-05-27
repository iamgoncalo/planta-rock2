"use client";

import { useState } from "react";
import { FESTIVAL_DAYS, getShowsForDay } from "@/lib/shows";
import { useCurrentShow } from "@/hooks/useCurrentShow";
import Programme from "@/components/shows/Programme";

const DAY_LABELS: Record<string, string> = {
  "2026-06-20": "20 Jun",
  "2026-06-21": "21 Jun",
  "2026-06-27": "27 Jun",
  "2026-06-28": "28 Jun",
};

export default function ShowsPage() {
  const today = new Date().toISOString().slice(0, 10);
  const defaultDay =
    FESTIVAL_DAYS.includes(today) ? today : FESTIVAL_DAYS[0];
  const [selectedDay, setSelectedDay] = useState(defaultDay);
  const { show_activo } = useCurrentShow();

  const shows = getShowsForDay(selectedDay);

  // Find current show ID
  const currentShow = shows.find(
    (s) => s.artista === show_activo
  );

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
          Programação
        </h1>
        <p className="text-sm" style={{ color: "#94a3b8" }}>
          Shows por dia — headliners e surge esperado
        </p>
      </div>

      {/* Day selector */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {FESTIVAL_DAYS.map((day) => (
          <button
            key={day}
            onClick={() => setSelectedDay(day)}
            className="px-4 py-2 rounded text-sm font-medium transition-colors"
            style={{
              backgroundColor:
                selectedDay === day ? "#4A7C59" : "#1a1f2e",
              color: selectedDay === day ? "#fff" : "#94a3b8",
              border: `1px solid ${
                selectedDay === day ? "#4A7C59" : "#2d3348"
              }`,
            }}
          >
            {DAY_LABELS[day] ?? day}
            {day === today && (
              <span
                className="ml-1.5 text-xs"
                style={{ color: selectedDay === day ? "#c5e8cf" : "#6FAF82" }}
              >
                hoje
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-4 text-xs flex-wrap">
        <span style={{ color: "#D48B3A" }}>★ Headliner</span>
        <span style={{ color: "#D48B3A" }}>⚡ Surge +30min</span>
        <span style={{ color: "#6FAF82" }}>AO VIVO actualmente</span>
      </div>

      <Programme shows={shows} currentShowId={currentShow?.id ?? null} />
    </div>
  );
}
