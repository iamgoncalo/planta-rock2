'use client'
import { useWS } from '@/context/WSContext'
import Gauge from '@/components/Gauge'
import type { Cluster } from '@/types/api'

function statusLabel(s: string) {
  return s === 'critico' ? 'CRÍTICO' : s === 'cheio' ? 'CHEIO' : s === 'moderado' ? 'MODERADO' : 'LIVRE'
}
function statusColor(s: string) {
  return s === 'critico' ? 'var(--critical)' : s === 'cheio' ? 'var(--amber)' : s === 'moderado' ? 'var(--gold)' : 'var(--green-bright)'
}

export default function OccupationPage() {
  const { clusters, status } = useWS()

  if (status !== 'live' && clusters.length === 0) {
    return (
      <div style={{padding:24,maxWidth:900,margin:'0 auto'}}>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(280px,1fr))',gap:16}}>
          {Array(8).fill(0).map((_,i)=><div key={i} className="skeleton" style={{height:220,borderRadius:12}}/>)}
        </div>
      </div>
    )
  }

  if (status !== 'live') {
    return <div style={{padding:24,textAlign:'center',color:'var(--text-soft)'}}>Sem dados ao vivo — sistema offline</div>
  }

  const sorted = [...clusters].sort((a: Cluster, b: Cluster) => {
    const aF = a.secoes?.F?.ocupacao_pct ?? a.secoes?.U?.ocupacao_pct ?? 0
    const bF = b.secoes?.F?.ocupacao_pct ?? b.secoes?.U?.ocupacao_pct ?? 0
    return aF - bF
  })

  return (
    <div style={{padding:16,maxWidth:900,margin:'0 auto'}}>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:20}}>
        <h1>Ocupação WC</h1>
        <span className="simulado-badge">SIMULADO</span>
      </div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(280px,1fr))',gap:16}}>
        {sorted.map((c: Cluster) => {
          const isUnisex = c.tipo === 'unissex'
          const u = c.secoes?.U
          const m = c.secoes?.M
          const f = c.secoes?.F
          const topStatus = isUnisex
            ? (u?.status || 'livre')
            : (m?.status === 'critico' || f?.status === 'critico'
                ? 'critico'
                : m?.status || f?.status || 'livre')
          return (
            <div key={c.cluster_id} id={c.cluster_id} className="card" style={{borderTop:`3px solid ${statusColor(topStatus)}`}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:12}}>
                <div>
                  <div style={{fontWeight:700,fontSize:20}}>{c.cluster_id}</div>
                  <div style={{fontSize:14,color:'var(--text-soft)'}}>{c.nome}</div>
                </div>
                <span style={{fontSize:12,fontWeight:700,color:statusColor(topStatus),background:`${statusColor(topStatus)}18`,padding:'3px 8px',borderRadius:4}}>
                  {statusLabel(topStatus)}
                </span>
              </div>
              {isUnisex ? (
                <div style={{display:'flex',justifyContent:'center',padding:'8px 0'}}>
                  <Gauge value={u?.ocupacao_pct||0} label="Unisex" size={130} />
                </div>
              ) : (
                <div style={{display:'flex',justifyContent:'space-around',padding:'8px 0'}}>
                  <Gauge value={m?.ocupacao_pct||0} label="♂" size={110} />
                  <Gauge value={f?.ocupacao_pct||0} label="♀" size={110} />
                </div>
              )}
              <div style={{display:'flex',gap:16,marginTop:12,fontSize:14,color:'var(--text-soft)'}}>
                <span>⏳ {isUnisex ? u?.fila_actual : ((m?.fila_actual||0)+(f?.fila_actual||0))} fila</span>
                <span>⏱ {isUnisex
                  ? (u?.tempo_espera_min||0).toFixed(1)
                  : (Math.max(m?.tempo_espera_min||0, f?.tempo_espera_min||0)).toFixed(1)}min</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
