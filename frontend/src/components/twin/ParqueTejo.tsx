"use client";

import { useState } from "react";
import type { ClusterData } from "@/types";
import { CLUSTER_SVG_POS } from "@/lib/clusters";
import ClusterDot from "./ClusterDot";
import ClusterDrawer from "./ClusterDrawer";

interface ParqueTejoProp {
  clusters: ClusterData[];
}

export default function ParqueTejo({ clusters }: ParqueTejoProp) {
  const [selected, setSelected] = useState<ClusterData | null>(null);

  const clusterMap = new Map(clusters.map((c) => [c.cluster_id, c]));

  return (
    <>
      <div
        style={{
          backgroundColor: "#1a1f2e",
          border: "1px solid #2d3348",
          borderRadius: 12,
          overflow: "hidden",
        }}
      >
        <svg
          viewBox="0 0 600 420"
          style={{ width: "100%", height: "auto", display: "block" }}
          aria-label="Mapa esquemático Parque Tejo"
        >
          {/* Background */}
          <rect width="600" height="420" fill="#0f1117" />

          {/* River / water area at bottom */}
          <rect x="0" y="370" width="600" height="50" fill="#0d1e33" opacity="0.8" />
          <text x="300" y="395" textAnchor="middle" fontSize="11" fill="#1e3a5f" fontStyle="italic">
            Rio Tejo
          </text>

          {/* Festival grounds outline */}
          <rect
            x="40" y="30" width="520" height="320"
            fill="none" stroke="#2d3348" strokeWidth="2" rx="8"
          />

          {/* Palco Mundo (main stage) */}
          <rect x="220" y="40" width="160" height="60" fill="#1e2a1e" stroke="#4A7C59" strokeWidth="1.5" rx="4" />
          <text x="300" y="68" textAnchor="middle" fontSize="11" fill="#6FAF82" fontWeight="bold">
            Palco Mundo
          </text>
          <text x="300" y="82" textAnchor="middle" fontSize="9" fill="#4A7C59">
            PM
          </text>

          {/* Palco Mundo Verde */}
          <rect x="430" y="50" width="100" height="45" fill="#1a2020" stroke="#3d6b3d" strokeWidth="1" rx="4" />
          <text x="480" y="70" textAnchor="middle" fontSize="9" fill="#5a9a5a">
            Palco Mundo Verde
          </text>
          <text x="480" y="83" textAnchor="middle" fontSize="8" fill="#3d6b3d">PMV</text>

          {/* Palco Super Bock */}
          <rect x="60" y="50" width="100" height="45" fill="#1a1a20" stroke="#3d3d6b" strokeWidth="1" rx="4" />
          <text x="110" y="70" textAnchor="middle" fontSize="9" fill="#6b6baa">
            Palco Super Bock
          </text>
          <text x="110" y="83" textAnchor="middle" fontSize="8" fill="#3d3d6b">PSB</text>

          {/* Main entrance */}
          <rect x="255" y="335" width="90" height="18" fill="#1e2a1e" stroke="#4A7C59" strokeWidth="1" rx="3" />
          <text x="300" y="348" textAnchor="middle" fontSize="9" fill="#6FAF82">
            Entrada Principal
          </text>

          {/* Zone A */}
          <rect x="350" y="130" width="180" height="140" fill="none" stroke="#2a3040" strokeWidth="1" strokeDasharray="4,3" rx="4" />
          <text x="440" y="148" textAnchor="middle" fontSize="9" fill="#2a3040">
            Zona A
          </text>

          {/* Zone B */}
          <rect x="60" y="150" width="170" height="130" fill="none" stroke="#2a3040" strokeWidth="1" strokeDasharray="4,3" rx="4" />
          <text x="145" y="168" textAnchor="middle" fontSize="9" fill="#2a3040">
            Zona B
          </text>

          {/* Zone C - central */}
          <rect x="240" y="150" width="100" height="120" fill="none" stroke="#2a3040" strokeWidth="1" strokeDasharray="4,3" rx="4" />
          <text x="290" y="168" textAnchor="middle" fontSize="9" fill="#2a3040">
            Zona C
          </text>

          {/* Food / vendor area */}
          <rect x="60" y="290" width="160" height="40" fill="#1a1e15" stroke="#3d4030" strokeWidth="1" rx="3" />
          <text x="140" y="314" textAnchor="middle" fontSize="9" fill="#4d5040">
            Alimentação / Vendors
          </text>

          {/* Walkway paths */}
          <line x1="300" y1="353" x2="300" y2="330" stroke="#2d3348" strokeWidth="2" />
          <line x1="80" y1="200" x2="540" y2="200" stroke="#1e2330" strokeWidth="1.5" strokeDasharray="6,4" />
          <line x1="300" y1="110" x2="300" y2="340" stroke="#1e2330" strokeWidth="1.5" strokeDasharray="6,4" />

          {/* Lockers area */}
          <rect x="170" y="280" width="60" height="30" fill="#151820" stroke="#2a2d38" strokeWidth="1" rx="2" />
          <text x="200" y="299" textAnchor="middle" fontSize="8" fill="#2a2d38">Cacifos</text>

          {/* Cluster dots */}
          {CLUSTER_IDS_ORDERED.map((id) => {
            const pos = CLUSTER_SVG_POS[id];
            const cluster = clusterMap.get(id);
            if (!pos || !cluster) return null;
            return (
              <ClusterDot
                key={id}
                cluster={cluster}
                x={pos.x}
                y={pos.y}
                onClick={setSelected}
              />
            );
          })}

          {/* Legend */}
          <g transform="translate(20, 385)">
            <circle cx="6" cy="6" r="5" fill="#6FAF82" />
            <text x="14" y="10" fontSize="8" fill="#6FAF82">Livre</text>
            <circle cx="50" cy="6" r="5" fill="#D48B3A" />
            <text x="58" y="10" fontSize="8" fill="#D48B3A">Moderado/Cheio</text>
            <circle cx="130" cy="6" r="5" fill="#C25A1A" />
            <text x="138" y="10" fontSize="8" fill="#C25A1A">Crítico</text>
            <circle cx="175" cy="6" r="5" fill="#6B7280" />
            <text x="183" y="10" fontSize="8" fill="#6B7280">Offline</text>
          </g>
        </svg>
      </div>

      <ClusterDrawer cluster={selected} onClose={() => setSelected(null)} />
    </>
  );
}

const CLUSTER_IDS_ORDERED = [
  "WC-01", "WC-02", "WC-03", "WC-04",
  "WC-05", "WC-06", "WC-07", "WC-08",
];
