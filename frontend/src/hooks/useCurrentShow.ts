"use client";

import { useState, useEffect } from "react";
import { getWSInstance } from "@/lib/ws";
import type { WebSocketPayload } from "@/types";

interface CurrentShowInfo {
  show_activo: string | null;
  minutos_para_headliner: number | null;
}

export function useCurrentShow() {
  const [info, setInfo] = useState<CurrentShowInfo>({
    show_activo: null,
    minutos_para_headliner: null,
  });

  useEffect(() => {
    const ws = getWSInstance();

    const onMessage = (payload: WebSocketPayload) => {
      setInfo({
        show_activo: payload.show_activo,
        minutos_para_headliner: payload.minutos_para_headliner,
      });
    };

    ws.addListener(onMessage);
    ws.connect();

    return () => {
      ws.removeListener(onMessage);
    };
  }, []);

  return info;
}
