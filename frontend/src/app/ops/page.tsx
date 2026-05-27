'use client'
import { useState } from 'react'
import { useWS } from '@/context/WSContext'
import type { AlertItem, Cluster, SectionState } from '@/types/api'

function sevColor(s: string) {
  return s==='CRITICO'?'var(--critical)':s==='ALTO'?'var(--amber)':s==='MEDIO'?'var(--gold)':'var(--text-soft)'
}

export default function OpsPage() {
  const { alerts, clusters, kpis } = useWS()
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  const active = alerts.filter((a: AlertItem) => !dismissed.has(`${a.cluster_id}-${a.ts}`))

  return (
    <div style={{padding:16,maxWidth:1200,margin:'0 auto'}}>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:20}}>
        <h1>Operações</h1>
        <span className="simulado-badge">SIMULADO</span>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr',gap:16}}>
        {/* KPI bar */}
        {kpis && (
          <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
            {[
              {label:'Flow Index', value:kpis.kpi_01?.toFixed(0)+'', unit:''},
              {label:'Util. Média', value:kpis.kpi_02?.toFixed(0)+'', unit:'%'},
              {label:'Alertas Críticos', value:''+kpis.kpi_03, unit:''},
              {label:'Redireccionados', value:''+kpis.kpi_04, unit:''},
            ].map(k => (
              <div key={k.label} className="card" style={{textAlign:'center'}}>
                <div style={{fontSize:13,color:'var(--text-soft)',marginBottom:4}}>{k.label}</div>
                <div className="mono display" style={{fontSize:'clamp(32px,8vw,48px)'}}>{k.value}{k.unit}</div>
              </div>
            ))}
          </div>
        )}

        {/* Alerts */}
        <div className="card">
          <h2 style={{marginBottom:12}}>Alertas Activos {active.length > 0 && <span style={{color:'var(--critical)'}}>({active.length})</span>}</h2>
          {active.length === 0 ? (
            <p style={{color:'var(--text-soft)'}}>Sem alertas activos.</p>
          ) : (
            <div style={{display:'flex',flexDirection:'column',gap:8}}>
              {active.map((a: AlertItem) => (
                <div key={`${a.cluster_id}-${a.ts}`} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'10px 14px',borderRadius:8,background:'var(--surface-2)',border:`1px solid ${sevColor(a.severidade)}40`}}>
                  <div>
                    <span style={{fontWeight:700,color:sevColor(a.severidade),marginRight:8}}>{a.severidade}</span>
                    <span style={{fontWeight:600,marginRight:8}}>{a.cluster_id}</span>
                    <span style={{color:'var(--text-soft)',fontSize:15}}>{a.mensagem}</span>
                  </div>
                  <button onClick={() => setDismissed(new Set([...dismissed, `${a.cluster_id}-${a.ts}`]))}
                    style={{padding:'6px 14px',borderRadius:6,border:'1px solid var(--border)',background:'var(--surface)',cursor:'pointer',fontSize:13,fontFamily:'DM Sans,sans-serif',minHeight:40}}>
                    Resolver
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Cluster grid */}
        <div className="card">
          <h2 style={{marginBottom:12}}>Estado Clusters</h2>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(200px,1fr))',gap:10}}>
            {clusters.map((c: Cluster) => {
              const secs = Object.values(c.secoes||{}) as SectionState[]
              const avgOcc = secs.length ? secs.reduce((a: number, s: SectionState) => a + (s.ocupacao_pct||0), 0) / secs.length : 0
              const statusColor = avgOcc >= 90 ? 'var(--critical)' : avgOcc >= 75 ? 'var(--amber)' : avgOcc >= 50 ? 'var(--gold)' : 'var(--green-bright)'
              return (
                <div key={c.cluster_id} style={{padding:'10px 14px',borderRadius:8,border:'1px solid var(--border)',background:'var(--surface-2)',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                  <span style={{fontWeight:600}}>{c.cluster_id}</span>
                  <span className="mono" style={{fontSize:18,color:statusColor}}>{avgOcc.toFixed(0)}%</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
