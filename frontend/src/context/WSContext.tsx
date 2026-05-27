'use client'
import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import type { Cluster, GlobalKPIs, AlertItem, WSPayload } from '@/types/api'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws'

export type WSStatus = 'connecting' | 'live' | 'reconnecting' | 'offline'

interface WSContextValue {
  status: WSStatus
  lastPayload: WSPayload | null
  clusters: Cluster[]
  kpis: GlobalKPIs | null
  alerts: AlertItem[]
}

const WSContext = createContext<WSContextValue>({
  status: 'connecting', lastPayload: null, clusters: [], kpis: null, alerts: []
})

export function WSProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<WSStatus>('connecting')
  const [lastPayload, setLastPayload] = useState<WSPayload | null>(null)
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [kpis, setKpis] = useState<GlobalKPIs | null>(null)
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const retryDelay = useRef(1000)

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close()
    setStatus('connecting')
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => { setStatus('live'); retryDelay.current = 1000 }
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as WSPayload
        setLastPayload(data)
        if (data.clusters) setClusters(data.clusters)
        if (data.kpis) setKpis(data.kpis)
        if (data.alertas_activos !== undefined) setAlerts([])
      } catch { /* ignore parse errors */ }
    }
    ws.onerror = () => setStatus('reconnecting')
    ws.onclose = () => {
      setStatus('reconnecting')
      retryRef.current = setTimeout(() => {
        retryDelay.current = Math.min(retryDelay.current * 2, 30000)
        connect()
      }, retryDelay.current)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      clearTimeout(retryRef.current)
    }
  }, [connect])

  return (
    <WSContext.Provider value={{ status, lastPayload, clusters, kpis, alerts }}>
      {children}
    </WSContext.Provider>
  )
}

export function useWS() { return useContext(WSContext) }
