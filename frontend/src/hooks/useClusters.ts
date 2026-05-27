"use client";

import { useState, useEffect, useCallback } from "react";
import { getWSInstance, type WSStatus } from "@/lib/ws";
import { fetchClusters } from "@/lib/api";
import type { ClusterData, WebSocketPayload } from "@/types";

export function useClusters() {
  const [clusters, setClusters] = useState<ClusterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<WSStatus>("disconnected");
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);

  const loadFromRest = useCallback(async () => {
    try {
      const data = await fetchClusters();
      setClusters(data.clusters);
      setLastUpdate(data.ts);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load clusters");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Load initial data from REST
    loadFromRest();

    const ws = getWSInstance();

    const onMessage = (payload: WebSocketPayload) => {
      setClusters(payload.clusters);
      setLastUpdate(payload.ts);
      setError(null);
      setLoading(false);
    };

    const onStatus = (status: WSStatus) => {
      setWsStatus(status);
      if (status === "disconnected" || status === "error") {
        // Fallback to REST polling when WS is down
        loadFromRest();
      }
    };

    ws.addListener(onMessage);
    ws.addStatusListener(onStatus);
    ws.connect();

    // Poll REST as fallback every 10s when WS is not connected
    const poll = setInterval(() => {
      if (wsStatus !== "connected") {
        loadFromRest();
      }
    }, 10000);

    return () => {
      ws.removeListener(onMessage);
      ws.removeStatusListener(onStatus);
      clearInterval(poll);
    };
  }, [loadFromRest, wsStatus]);

  return { clusters, loading, error, wsStatus, lastUpdate, refetch: loadFromRest };
}
