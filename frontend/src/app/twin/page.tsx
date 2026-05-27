'use client'
import { useState } from 'react'
import { useWS } from '@/context/WSContext'
import type { Cluster, SectionState } from '@/types/api'

// Venue footprint 530×380m, normalized to SVG 530×380 viewBox
// Cluster positions in metres (approx from lat/lon)
const clusterPositions: Record<string,{x:number,y:number}> = {
  'WC-01':{x:420,y:80}, 'WC-02':{x:390,y:120}, 'WC-03':{x:330,y:200},
  'WC-04':{x:360,y:130}, 'WC-05':{x:340,y:170}, 'WC-06':{x:100,y:310},
  'WC-07':{x:270,y:270}, 'WC-08':{x:60,y:360},
}

function occColor(pct: number) {
  return pct >= 90 ? '#C25A1A' : pct >= 75 ? '#D48B3A' : pct >= 50 ? '#D4A82A' : '#6FAF82'
}

export default function TwinPage() {
  const { clusters, status, lastPayload } = useWS()
  const [selected, setSelected] = useState<Cluster | null>(null)

  if (status !== 'live' && clusters.length === 0) {
    return <div style={{padding:24,color:'var(--text-soft)'}}>Backend indisponível, tente novamente em 5s</div>
  }

  return (
    <div style={{padding:16,maxWidth:900,margin:'0 auto'}}>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:12}}>
        <h1>Digital Twin</h1>
        <span className="simulado-badge">SIMULADO</span>
      </div>

      {lastPayload?.show_activo && (
        <div style={{background:'var(--surface-2)',borderRadius:8,padding:'8px 14px',marginBottom:12,fontSize:15}}>
          ▶ {lastPayload.show_activo}
        </div>
      )}

      <div style={{position:'relative',background:'var(--surface-2)',borderRadius:12,overflow:'hidden'}}>
        <svg viewBox="0 0 530 380" style={{width:'100%',maxHeight:400,display:'block'}}>
          {/* Venue outline */}
          <rect x={10} y={10} width={510} height={360} rx={8} fill="none" stroke="var(--border)" strokeWidth={2}/>
          {/* Stage labels */}
          <text x={265} y={40} textAnchor="middle" fontSize={12} fill="var(--text-soft)">PALCO MUNDO</text>
          <rect x={200} y={45} width={130} height={50} rx={4} fill="var(--border)" opacity={0.4}/>
          <text x={265} y={100} textAnchor="middle" fontSize={10} fill="var(--text-soft)">MUSIC VALLEY</text>
          <rect x={200} y={150} width={80} height={35} rx={4} fill="var(--border)" opacity={0.3}/>

          {/* WC cluster dots */}
          {clusters.map((c: Cluster) => {
            const pos = clusterPositions[c.cluster_id]
            if (!pos) return null
            const secs = c.secoes || {}
            const vals = Object.values(secs) as SectionState[]
            const avgOcc = vals.length ? vals.reduce((a: number, s: SectionState) => a + (s.ocupacao_pct||0), 0) / vals.length : 0
            const r = 12 + avgOcc / 14
            return (
              <g key={c.cluster_id} onClick={() => setSelected(selected?.cluster_id === c.cluster_id ? null : c)} style={{cursor:'pointer'}}>
                <circle cx={pos.x} cy={pos.y} r={r+4} fill={occColor(avgOcc)} opacity={0.15}/>
                <circle cx={pos.x} cy={pos.y} r={r} fill={occColor(avgOcc)} opacity={0.9}/>
                <text x={pos.x} y={pos.y+4} textAnchor="middle" fontSize={9} fill="#fff" fontWeight="700">{c.cluster_id.replace('WC-','')}</text>
              </g>
            )
          })}
        </svg>

        {/* Legend */}
        <div style={{padding:'8px 12px',display:'flex',gap:16,fontSize:12,color:'var(--text-soft)'}}>
          {[['#6FAF82','Livre'],['#D4A82A','Moderado'],['#D48B3A','Cheio'],['#C25A1A','Crítico']].map(([c,l])=>(
            <span key={l} style={{display:'flex',alignItems:'center',gap:4}}>
              <span style={{width:10,height:10,borderRadius:'50%',background:c,display:'inline-block'}}/>
              {l}
            </span>
          ))}
        </div>
      </div>

      {/* Selected cluster drawer */}
      {selected && (
        <div className="card" style={{marginTop:16}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
            <h2>{selected.cluster_id} — {selected.nome}</h2>
            <button onClick={() => setSelected(null)} style={{background:'none',border:'none',fontSize:20,cursor:'pointer',color:'var(--text-soft)'}}>✕</button>
          </div>
          {Object.entries(selected.secoes||{}).map(([key, sec]) => (
            <div key={key} style={{padding:'8px 0',borderTop:'1px solid var(--border)',display:'flex',justifyContent:'space-between',fontSize:16}}>
              <span style={{fontWeight:500}}>{key === 'U' ? 'Unisex' : key === 'M' ? '♂ Masculino' : '♀ Feminino'}</span>
              <span className="mono" style={{color:occColor((sec as SectionState).ocupacao_pct)}}>{(sec as SectionState).ocupacao_pct.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
