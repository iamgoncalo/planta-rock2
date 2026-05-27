"use client";

import { useClusters } from "@/hooks/useClusters";
import { useKPIs } from "@/hooks/useKPIs";
import { useCurrentShow } from "@/hooks/useCurrentShow";
import ChatWindow from "@/components/chat/ChatWindow";

export default function ChatPage() {
  const { clusters } = useClusters();
  const { kpis } = useKPIs();
  const { show_activo } = useCurrentShow();

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
          Chat Operacional
        </h1>
        <p className="text-sm" style={{ color: "#94a3b8" }}>
          Assistente com contexto live dos WCs e shows
        </p>
      </div>

      <div
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          borderRadius: 12,
          padding: 16,
          height: "calc(100vh - 280px)",
          minHeight: 500,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <ChatWindow
          clusters={clusters}
          kpis={kpis}
          showActivo={show_activo}
        />
      </div>
    </div>
  );
}
