"use client";

import { useEffect, useState } from "react";
import { getWSInstance, type WSStatus } from "@/lib/ws";
import { useCurrentShow } from "@/hooks/useCurrentShow";

function LiveClock() {
  const [time, setTime] = useState<string>("");

  useEffect(() => {
    const update = () => {
      setTime(
        new Date().toLocaleTimeString("pt-PT", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    };
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);

  return <span>{time}</span>;
}

function WSStatusBadge({ status }: { status: WSStatus }) {
  const color =
    status === "connected"
      ? "#6FAF82"
      : status === "connecting"
        ? "#D48B3A"
        : "#6B7280";
  const label =
    status === "connected"
      ? "LIVE"
      : status === "connecting"
        ? "CONN..."
        : "OFFLINE";

  return (
    <span className="flex items-center gap-1.5">
      <span
        className={status === "connected" ? "animate-pulse" : ""}
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          backgroundColor: color,
          display: "inline-block",
        }}
      />
      <span className="text-xs font-mono" style={{ color }}>
        {label}
      </span>
    </span>
  );
}

export default function StatusBar() {
  const [wsStatus, setWsStatus] = useState<WSStatus>("disconnected");
  const { show_activo, minutos_para_headliner } = useCurrentShow();

  useEffect(() => {
    const ws = getWSInstance();
    setWsStatus(ws.getStatus());
    const onStatus = (s: WSStatus) => setWsStatus(s);
    ws.addStatusListener(onStatus);
    ws.connect();
    return () => ws.removeStatusListener(onStatus);
  }, []);

  return (
    <div
      style={{
        backgroundColor: "#0d1018",
        borderBottom: "1px solid #2d3348",
        color: "#94a3b8",
      }}
      className="text-xs"
    >
      <div className="max-w-screen-xl mx-auto px-4 py-1.5 flex items-center gap-4 flex-wrap">
        <WSStatusBadge status={wsStatus} />
        <span className="font-mono">
          <LiveClock />
        </span>
        {show_activo && (
          <span style={{ color: "#6FAF82" }}>
            ♪ {show_activo}
            {minutos_para_headliner !== null && minutos_para_headliner > 0 && (
              <span style={{ color: "#D48B3A" }}>
                {" "}
                · headliner em {minutos_para_headliner}min
              </span>
            )}
          </span>
        )}
        {!show_activo && (
          <span style={{ color: "#4b5563" }}>Sem show activo</span>
        )}
        <span className="ml-auto" style={{ color: "#2d3348" }}>
          PlantaOS v1.0.0
        </span>
      </div>
    </div>
  );
}
