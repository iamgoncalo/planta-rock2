"use client";

import { useState, useRef, useEffect } from "react";
import { postChat } from "@/lib/api";
import type { ChatMessage, ClusterData, GlobalKPIs } from "@/types";

interface ChatWindowProps {
  clusters: ClusterData[];
  kpis: GlobalKPIs | null;
  showActivo: string | null;
}

function buildContext(clusters: ClusterData[], kpis: GlobalKPIs | null, showActivo: string | null): string {
  const parts: string[] = [];

  if (showActivo) {
    parts.push(`Show activo: ${showActivo}`);
  }

  if (kpis) {
    parts.push(
      `KPIs: Fluxo ${kpis.kpi_01.toFixed(0)}/100, Ocupação média ${kpis.kpi_02.toFixed(0)}%, Alertas críticos: ${kpis.kpi_03}, Redirecionados hoje: ${kpis.kpi_04}`
    );
  }

  const clusterSummaries = clusters
    .map((c) => {
      const sections = Object.entries(c.secoes)
        .filter(([, s]) => s !== undefined)
        .map(([k, s]) => {
          const secLabel = k === "U" ? "Unissex" : k === "M" ? "Masc" : "Fem";
          return `${secLabel}: ${s!.ocupacao_pct.toFixed(0)}% (status: ${s!.status})`;
        })
        .join(", ");
      return `${c.cluster_id} (${c.nome}): ${sections}`;
    })
    .join("; ");

  if (clusterSummaries) {
    parts.push(`Estado WCs: ${clusterSummaries}`);
  }

  return parts.join("\n");
}

export default function ChatWindow({ clusters, kpis, showActivo }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const context = buildContext(clusters, kpis, showActivo);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const resp = await postChat({ message: text, context });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: resp.reply },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Não foi possível obter resposta do servidor. Verifica se o backend está online.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div
      className="flex flex-col h-full"
      style={{ minHeight: 0 }}
    >
      {/* Context badge */}
      <div
        className="p-3 mb-3 rounded text-xs"
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          color: "#94a3b8",
        }}
      >
        <span style={{ color: "#6FAF82" }} className="font-semibold">
          Contexto ao vivo:{" "}
        </span>
        <span>
          {clusters.length} clusters monitorizados
          {showActivo ? ` · Show: ${showActivo}` : " · Sem show activo"}
          {kpis
            ? ` · Ocupação média: ${kpis.kpi_02.toFixed(0)}% · Alertas: ${kpis.kpi_03}`
            : ""}
        </span>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto flex flex-col gap-3 p-1"
        style={{ minHeight: 0 }}
      >
        {messages.length === 0 && (
          <div
            className="text-center py-16 text-sm"
            style={{ color: "#4b5563" }}
          >
            <p className="text-2xl mb-3">💬</p>
            <p>Pergunta sobre o estado actual dos WCs,</p>
            <p>alertas, fluxos ou recomendações de routing.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className="max-w-xs md:max-w-md lg:max-w-lg rounded-xl px-4 py-2.5 text-sm"
              style={{
                backgroundColor:
                  msg.role === "user" ? "#4A7C59" : "#1a1f2e",
                color: "#e2e8f0",
                border:
                  msg.role === "assistant"
                    ? "1px solid #2d3348"
                    : "none",
                borderRadius:
                  msg.role === "user"
                    ? "18px 18px 4px 18px"
                    : "18px 18px 18px 4px",
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div
              className="rounded-xl px-4 py-2.5 text-sm"
              style={{
                backgroundColor: "#1a1f2e",
                border: "1px solid #2d3348",
                color: "#94a3b8",
              }}
            >
              <span className="inline-flex gap-1">
                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>●</span>
                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>●</span>
                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>●</span>
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        className="mt-3 flex gap-2"
        style={{ borderTop: "1px solid #2d3348", paddingTop: 12 }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Pergunta sobre os WCs, alertas ou fluxos..."
          rows={2}
          className="flex-1 resize-none rounded-lg px-3 py-2 text-sm focus:outline-none"
          style={{
            backgroundColor: "#1a1f2e",
            border: "1px solid #2d3348",
            color: "#e2e8f0",
          }}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="px-4 py-2 rounded-lg text-sm font-semibold self-end transition-opacity"
          style={{
            backgroundColor: "#4A7C59",
            color: "#fff",
            opacity: !input.trim() || loading ? 0.5 : 1,
          }}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
