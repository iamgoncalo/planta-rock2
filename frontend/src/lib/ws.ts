"use client";

import type { WebSocketPayload } from "@/types";

type Listener = (payload: WebSocketPayload) => void;
type StatusListener = (status: WSStatus) => void;

export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

class WebSocketSingleton {
  private ws: WebSocket | null = null;
  private listeners: Set<Listener> = new Set();
  private statusListeners: Set<StatusListener> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private maxDelay = 30000;
  private status: WSStatus = "disconnected";
  private url: string;
  private shouldConnect = false;

  constructor() {
    this.url =
      (typeof window !== "undefined"
        ? process.env.NEXT_PUBLIC_WS_URL
        : undefined) ?? "ws://localhost:8000/api/v1/ws";
  }

  private setStatus(s: WSStatus) {
    this.status = s;
    this.statusListeners.forEach((l) => l(s));
  }

  connect() {
    this.shouldConnect = true;
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) return;
    this.tryConnect();
  }

  private tryConnect() {
    if (!this.shouldConnect) return;
    if (typeof window === "undefined") return;

    this.setStatus("connecting");
    try {
      this.ws = new WebSocket(this.url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this.setStatus("connected");
    };

    this.ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data as string) as WebSocketPayload;
        if (data.type === "cluster_update") {
          this.listeners.forEach((l) => l(data));
        }
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onerror = () => {
      this.setStatus("error");
    };

    this.ws.onclose = () => {
      this.setStatus("disconnected");
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (!this.shouldConnect) return;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.tryConnect();
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
  }

  disconnect() {
    this.shouldConnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  addListener(fn: Listener) {
    this.listeners.add(fn);
  }

  removeListener(fn: Listener) {
    this.listeners.delete(fn);
  }

  addStatusListener(fn: StatusListener) {
    this.statusListeners.add(fn);
  }

  removeStatusListener(fn: StatusListener) {
    this.statusListeners.delete(fn);
  }

  getStatus(): WSStatus {
    return this.status;
  }
}

// Singleton instance
let _instance: WebSocketSingleton | null = null;

export function getWSInstance(): WebSocketSingleton {
  if (!_instance) {
    _instance = new WebSocketSingleton();
  }
  return _instance;
}
