"use client";

import { useEffect, useState } from "react";
import type { ClusterData } from "@/types";
import { getWSInstance } from "@/lib/ws";

interface LogEntry {
  id: string;
  ts: number;
  cluster_id: string;
  event: string;
  value: string;
  color: string;
}

function formatAge(ts: number): string {
  const diff = Math.floor((Date.now() / 1000) - ts);
  if (diff < 60) return `há ${diff}s`;
  if (diff < 3600) return `há ${Math.floor(diff / 60)}min`;
  return `há ${Math.floor(diff / 3600)}h`;
}

export default function EventLog({ clusters }: { clusters: ClusterData[] }) {
  const [log, setLog] = useState<LogEntry[]>([]);

  // Generate log entries from clusters
  useEffect(() => {
    const entries: LogEntry[] = [];

    clusters.forEach((c) => {
      Object.entries(c.secoes).forEach(([key, sec]) => {
        if (!sec) return;
        const secLabel = key === "U" ? "Unissex" : key === "M" ? "Masc." : "Fem.";
        const baseId = `${c.cluster_id}-${key}`;

        entries.push({
          id: `${baseId}-flow-in`,
          ts: Math.floor(Date.now() / 1000) - Math.floor(Math.random() * 120),
          cluster_id: c.cluster_id,
          event: `IR Entrada [${secLabel}]`,
          value: `${sec.fluxo_entrada_pmin.toFixed(1)} p/min`,
          color: "#6FAF82",
        });

        entries.push({
          id: `${baseId}-flow-out`,
          ts: Math.floor(Date.now() / 1000) - Math.floor(Math.random() * 120),
          cluster_id: c.cluster_id,
          event: `IR Saída [${secLabel}]`,
          value: `${sec.fluxo_saida_pmin.toFixed(1)} p/min`,
          color: "#D48B3A",
        });

        if (sec.fontes_activas.includes("WiFi")) {
          entries.push({
            id: `${baseId}-wifi`,
            ts: Math.floor(Date.now() / 1000) - Math.floor(Math.random() * 300),
            cluster_id: c.cluster_id,
            event: `LilyGo WiFi [${secLabel}]`,
            value: `${sec.ocupacao_absoluta} pessoas`,
            color: "#60a5fa",
          });
        }
      });

      // Alert events
      c.alertas
        .filter((a) => !a.resolvido)
        .forEach((alert) => {
          entries.push({
            id: `alert-${alert.id}`,
            ts: alert.ts_inicio,
            cluster_id: c.cluster_id,
            event: `Alerta ${alert.severidade}`,
            value: alert.mensagem,
            color: alert.severidade === "CRITICO" ? "#C25A1A" : "#D48B3A",
          });
        });
    });

    // Sort by ts desc, take last 20
    entries.sort((a, b) => b.ts - a.ts);
    setLog(entries.slice(0, 20));
  }, [clusters]);

  // Subscribe to WS for new events
  useEffect(() => {
    const ws = getWSInstance();
    ws.connect();
  }, []);

  return (
    <div
      style={{
        backgroundColor: "#1a1f2e",
        border: "1px solid #2d3348",
        borderRadius: 8,
        overflow: "hidden",
      }}
    >
      <div
        className="px-4 py-2 flex items-center justify-between"
        style={{ backgroundColor: "#13161f", borderBottom: "1px solid #2d3348" }}
      >
        <h3 className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>
          Log de Eventos
        </h3>
        <span className="text-xs" style={{ color: "#94a3b8" }}>
          últimos {log.length} eventos
        </span>
      </div>
      <div className="divide-y" style={{ borderColor: "#1e2330" }}>
        {log.length === 0 && (
          <div className="px-4 py-8 text-center text-sm" style={{ color: "#4b5563" }}>
            Sem eventos recentes
          </div>
        )}
        {log.map((entry) => (
          <div
            key={entry.id}
            className="px-4 py-2 grid text-xs"
            style={{ gridTemplateColumns: "80px 80px 1fr 100px" }}
          >
            <span className="font-mono" style={{ color: "#94a3b8" }}>
              {formatAge(entry.ts)}
            </span>
            <span className="font-bold" style={{ color: "#e2e8f0" }}>
              {entry.cluster_id}
            </span>
            <span style={{ color: entry.color }}>{entry.event}</span>
            <span className="font-mono text-right" style={{ color: "#e2e8f0" }}>
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
