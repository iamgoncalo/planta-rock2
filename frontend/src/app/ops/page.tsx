"use client";

import { useState, useEffect, useCallback } from "react";
import { useClusters } from "@/hooks/useClusters";
import { useAlerts } from "@/hooks/useAlerts";
import { getWSInstance } from "@/lib/ws";
import type { RoutingRecommendation } from "@/types";
import AlertList from "@/components/ops/AlertList";
import RoutingPanel from "@/components/ops/RoutingPanel";

function generateCSV(
  clusters: ReturnType<typeof useClusters>["clusters"]
): string {
  const rows: string[][] = [
    [
      "cluster_id",
      "nome",
      "tipo",
      "secao",
      "ocupacao_pct",
      "ocupacao_absoluta",
      "fila_actual",
      "tempo_espera_min",
      "fluxo_entrada_pmin",
      "fluxo_saida_pmin",
      "status",
      "confianca_pct",
      "fontes_activas",
    ],
  ];

  for (const c of clusters) {
    for (const [key, sec] of Object.entries(c.secoes)) {
      if (!sec) continue;
      const secLabel = key === "U" ? "Unissex" : key === "M" ? "Masculino" : "Feminino";
      rows.push([
        c.cluster_id,
        c.nome,
        c.tipo,
        secLabel,
        sec.ocupacao_pct.toFixed(1),
        String(sec.ocupacao_absoluta),
        String(sec.fila_actual),
        sec.tempo_espera_min.toFixed(1),
        sec.fluxo_entrada_pmin.toFixed(2),
        sec.fluxo_saida_pmin.toFixed(2),
        sec.status,
        sec.confianca_pct.toFixed(0),
        sec.fontes_activas.join("|"),
      ]);
    }
  }

  return rows.map((r) => r.join(",")).join("\n");
}

export default function OpsPage() {
  const { clusters, wsStatus } = useClusters();
  const { alerts, resolveAlert } = useAlerts();
  const [routing, setRouting] = useState<RoutingRecommendation[]>([]);
  const [lastScorPush, setLastScorPush] = useState<number>(Date.now() / 1000);
  const [scorStatus, setScorStatus] = useState<number>(200);

  // Subscribe to routing recs from WS
  useEffect(() => {
    const ws = getWSInstance();
    const handler = (payload: { routing_recommendations?: RoutingRecommendation[] }) => {
      if (payload.routing_recommendations) {
        setRouting(payload.routing_recommendations);
        setLastScorPush(Date.now() / 1000);
        setScorStatus(200);
      }
    };
    ws.addListener(handler as Parameters<typeof ws.addListener>[0]);
    ws.connect();
    return () => ws.removeListener(handler as Parameters<typeof ws.addListener>[0]);
  }, []);

  const handleExport = useCallback(() => {
    const csv = generateCSV(clusters);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `plantaos-export-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [clusters]);

  const onlineClusters = clusters.filter((c) => {
    const sections = Object.values(c.secoes).filter(Boolean);
    return sections.some((s) => s?.status !== "offline");
  }).length;

  const irOnline = clusters.reduce((sum, c) => {
    return (
      sum +
      Object.values(c.secoes).filter(
        (s) => s?.fontes_activas.includes("IR")
      ).length * 2
    );
  }, 0);

  const scorAge = Math.floor(Date.now() / 1000 - lastScorPush);
  const scorAgeStr =
    scorAge < 60 ? `${scorAge}s` : `${Math.floor(scorAge / 60)}min`;

  return (
    <div>
      <div className="flex items-start justify-between mb-4 flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
            Operações
          </h1>
          <p className="text-sm" style={{ color: "#94a3b8" }}>
            Alertas, routing e estado da rede de sensores
          </p>
        </div>
        <button
          onClick={handleExport}
          className="px-4 py-2 rounded text-sm font-medium"
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            color: "#94a3b8",
          }}
        >
          Exportar CSV
        </button>
      </div>

      {/* Network health bar */}
      <div
        className="mb-4 p-3 rounded-lg flex flex-wrap gap-4 text-xs"
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
        }}
      >
        <span>
          <span style={{ color: "#94a3b8" }}>Rede: </span>
          <span style={{ color: onlineClusters > 0 ? "#6FAF82" : "#C25A1A" }}>
            {onlineClusters}/{clusters.length} clusters online
          </span>
        </span>
        <span>
          <span style={{ color: "#94a3b8" }}>Sensores IR: </span>
          <span style={{ color: irOnline > 0 ? "#6FAF82" : "#C25A1A" }}>
            {irOnline}/24 online
          </span>
        </span>
        <span>
          <span style={{ color: "#94a3b8" }}>WebSocket: </span>
          <span
            style={{
              color:
                wsStatus === "connected"
                  ? "#6FAF82"
                  : wsStatus === "connecting"
                    ? "#D48B3A"
                    : "#C25A1A",
            }}
          >
            {wsStatus}
          </span>
        </span>
        <span>
          <span style={{ color: "#94a3b8" }}>SCOR: </span>
          <span style={{ color: "#6FAF82" }}>
            último push há {scorAgeStr} · HTTP {scorStatus}
          </span>
        </span>
      </div>

      {/* Main two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts */}
        <div
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            borderRadius: 10,
            padding: 16,
          }}
        >
          <AlertList alerts={alerts} onResolve={resolveAlert} />
        </div>

        {/* Routing */}
        <div
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            borderRadius: 10,
            padding: 16,
          }}
        >
          <RoutingPanel recommendations={routing} />
        </div>
      </div>

      {/* Timeline */}
      <div
        className="mt-6"
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          borderRadius: 10,
          padding: 16,
        }}
      >
        <h2 className="font-bold text-sm mb-3" style={{ color: "#e2e8f0" }}>
          Timeline do Dia
        </h2>
        <div className="flex flex-col gap-2 text-xs" style={{ color: "#94a3b8" }}>
          <div className="flex gap-3">
            <span className="font-mono w-12">18:00</span>
            <span>Abertura de portas — monitorização iniciada</span>
          </div>
          <div className="flex gap-3">
            <span className="font-mono w-12">18:30</span>
            <span>Primeiro show — clusters activados</span>
          </div>
          <div className="flex gap-3">
            <span className="font-mono w-12">21:00</span>
            <span>Headliner — surge esperado + 30min</span>
          </div>
          {alerts.slice(0, 5).map((a) => (
            <div key={a.id} className="flex gap-3">
              <span className="font-mono w-12">
                {new Date(a.ts_inicio * 1000).toLocaleTimeString("pt-PT", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
              <span
                style={{
                  color: a.severidade === "CRITICO" ? "#C25A1A" : "#D48B3A",
                }}
              >
                [{a.severidade}] {a.cluster_id} — {a.mensagem}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
