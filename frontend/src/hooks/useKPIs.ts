"use client";

import { useState, useEffect, useCallback } from "react";
import { getWSInstance } from "@/lib/ws";
import { fetchKPIs } from "@/lib/api";
import type { GlobalKPIs, WebSocketPayload } from "@/types";

export function useKPIs() {
  const [kpis, setKpis] = useState<GlobalKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFromRest = useCallback(async () => {
    try {
      const data = await fetchKPIs();
      setKpis(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load KPIs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFromRest();

    const ws = getWSInstance();

    const onMessage = (payload: WebSocketPayload) => {
      setKpis(payload.kpis);
      setLoading(false);
    };

    ws.addListener(onMessage);
    ws.connect();

    const poll = setInterval(loadFromRest, 15000);

    return () => {
      ws.removeListener(onMessage);
      clearInterval(poll);
    };
  }, [loadFromRest]);

  return { kpis, loading, error, refetch: loadFromRest };
}
