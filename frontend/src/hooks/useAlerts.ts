"use client";

import { useState, useEffect, useCallback } from "react";
import { getWSInstance } from "@/lib/ws";
import { fetchClusters } from "@/lib/api";
import type { Alert, WebSocketPayload } from "@/types";

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());

  const extractAlerts = useCallback(
    (clusters: WebSocketPayload["clusters"]) => {
      const all: Alert[] = [];
      for (const c of clusters) {
        for (const a of c.alertas) {
          if (!a.resolvido && !resolvedIds.has(a.id)) {
            all.push(a);
          }
        }
      }
      // Sort by severity
      const order: Record<string, number> = {
        CRITICO: 0,
        ALTO: 1,
        MEDIO: 2,
        INFO: 3,
      };
      all.sort(
        (a, b) =>
          (order[a.severidade] ?? 4) - (order[b.severidade] ?? 4)
      );
      setAlerts(all);
    },
    [resolvedIds]
  );

  const loadFromRest = useCallback(async () => {
    try {
      const data = await fetchClusters();
      extractAlerts(data.clusters);
    } catch {
      // silently fail
    }
  }, [extractAlerts]);

  useEffect(() => {
    loadFromRest();

    const ws = getWSInstance();

    const onMessage = (payload: WebSocketPayload) => {
      extractAlerts(payload.clusters);
    };

    ws.addListener(onMessage);
    ws.connect();

    return () => {
      ws.removeListener(onMessage);
    };
  }, [loadFromRest, extractAlerts]);

  const resolveAlert = useCallback((id: string) => {
    setResolvedIds((prev) => {
      const next = new Set(Array.from(prev));
      next.add(id);
      return next;
    });
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  return { alerts, resolveAlert };
}
