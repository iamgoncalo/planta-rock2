"use client";

import type { Alert } from "@/types";
import { getSeverityStyle } from "@/lib/colors";

interface AlertListProps {
  alerts: Alert[];
  onResolve: (id: string) => void;
}

function formatAge(ts: number): string {
  const diff = Math.floor(Date.now() / 1000 - ts);
  if (diff < 60) return `há ${diff}s`;
  if (diff < 3600) return `há ${Math.floor(diff / 60)}min`;
  return `há ${Math.floor(diff / 3600)}h`;
}

export default function AlertList({ alerts, onResolve }: AlertListProps) {
  const criticals = alerts.filter((a) => a.severidade === "CRITICO");
  const others = alerts.filter((a) => a.severidade !== "CRITICO");

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-bold text-sm" style={{ color: "#e2e8f0" }}>
          Alertas Activos
        </h2>
        <span
          className="text-xs px-2 py-0.5 rounded"
          style={{
            backgroundColor: alerts.length > 0 ? "#C25A1A22" : "#2d3348",
            color: alerts.length > 0 ? "#C25A1A" : "#94a3b8",
          }}
        >
          {alerts.length} activos
        </span>
      </div>

      {alerts.length === 0 && (
        <div
          className="py-8 text-center text-sm rounded-lg"
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            color: "#4b5563",
          }}
        >
          Sem alertas activos
        </div>
      )}

      {/* Critical alerts */}
      {criticals.map((alert) => {
        const style = getSeverityStyle(alert.severidade);
        return (
          <div
            key={alert.id}
            className="mb-2 p-3 rounded-lg"
            style={{
              backgroundColor: style.bg,
              border: `1px solid ${style.border}`,
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span
                    className="text-xs font-bold px-1.5 py-0.5 rounded"
                    style={{
                      backgroundColor: style.border,
                      color: "#fff",
                    }}
                  >
                    {alert.severidade}
                  </span>
                  <span
                    className="text-xs font-bold"
                    style={{ color: "#e2e8f0" }}
                  >
                    {alert.cluster_id}
                  </span>
                  <span className="text-xs" style={{ color: "#94a3b8" }}>
                    Secção{" "}
                    {alert.secao === "U"
                      ? "Unissex"
                      : alert.secao === "M"
                        ? "Masculino"
                        : alert.secao === "F"
                          ? "Feminino"
                          : "Global"}
                  </span>
                </div>
                <p className="text-sm" style={{ color: "#e2e8f0" }}>
                  {alert.mensagem}
                </p>
                <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>
                  {alert.tipo} · {formatAge(alert.ts_inicio)}
                </p>
              </div>
              <button
                onClick={() => onResolve(alert.id)}
                className="text-xs px-2 py-1 rounded shrink-0"
                style={{
                  backgroundColor: "#2d3348",
                  color: "#e2e8f0",
                  border: "1px solid #3d4558",
                }}
              >
                Resolver
              </button>
            </div>
          </div>
        );
      })}

      {/* Other alerts */}
      {others.map((alert) => {
        const style = getSeverityStyle(alert.severidade);
        return (
          <div
            key={alert.id}
            className="mb-2 p-3 rounded-lg"
            style={{
              backgroundColor: "#1a1f2e",
              border: `1px solid ${style.border}44`,
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span
                    className="text-xs font-semibold px-1.5 py-0.5 rounded"
                    style={{
                      backgroundColor: `${style.border}22`,
                      color: style.text,
                    }}
                  >
                    {alert.severidade}
                  </span>
                  <span
                    className="text-xs font-bold"
                    style={{ color: "#e2e8f0" }}
                  >
                    {alert.cluster_id}
                  </span>
                  <span className="text-xs" style={{ color: "#94a3b8" }}>
                    {alert.secao === "U"
                      ? "Unissex"
                      : alert.secao === "M"
                        ? "Masc"
                        : alert.secao === "F"
                          ? "Fem"
                          : "Global"}
                  </span>
                </div>
                <p className="text-sm" style={{ color: "#e2e8f0" }}>
                  {alert.mensagem}
                </p>
                <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>
                  {alert.tipo} · {formatAge(alert.ts_inicio)}
                </p>
              </div>
              <button
                onClick={() => onResolve(alert.id)}
                className="text-xs px-2 py-1 rounded shrink-0"
                style={{
                  backgroundColor: "#2d3348",
                  color: "#94a3b8",
                  border: "1px solid #3d4558",
                }}
              >
                Resolver
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
