"use client";

import { useClusters } from "@/hooks/useClusters";
import SensorTable from "@/components/sensors/SensorTable";
import EventLog from "@/components/sensors/EventLog";

export default function SensoresPage() {
  const { clusters, loading, error } = useClusters();

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
          Sensores
        </h1>
        <p className="text-sm" style={{ color: "#94a3b8" }}>
          Estado de cada sensor IR, LilyGo e câmara por cluster
        </p>
      </div>

      {error && (
        <div
          className="mb-4 p-3 rounded-lg text-sm"
          style={{
            backgroundColor: "#C25A1A22",
            border: "1px solid #C25A1A44",
            color: "#C25A1A",
          }}
        >
          Backend inacessível — {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                backgroundColor: "#1a1f2e",
                borderRadius: 8,
                height: 56,
              }}
              className="animate-pulse"
            />
          ))}
        </div>
      ) : (
        <>
          <SensorTable clusters={clusters} />
          <div className="mt-6">
            <EventLog clusters={clusters} />
          </div>
        </>
      )}
    </div>
  );
}
