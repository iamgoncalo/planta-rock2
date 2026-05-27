'use client'
import { use, useEffect, useState } from 'react'
import { useWS } from '@/context/WSContext'
import type { TVScreenState, TVClusterEntry } from '@/types/api'

function occColor(s: string) {
  return s === 'critico' ? '#C25A1A' : s === 'cheio' ? '#D48B3A' : s === 'moderado' ? '#D4A82A' : '#4A7C59'
}

function AltCard({ alt }: { alt: TVClusterEntry }) {
  return (
    <div style={{background:'var(--surface)',borderRadius:12,padding:'16px 24px',border:'1px solid var(--border)',minWidth:160}}>
      <div style={{fontSize:24,fontWeight:700,color:occColor(alt.status)}}>{alt.cluster_id}</div>
      <div style={{fontSize:16,color:'var(--text-soft)'}}>{Math.round((alt.walk_time_s + alt.queue_wait_s) / 60)}min total</div>
    </div>
  )
}

export default function TVPage({ params }: { params: Promise<{screen_id:string}> }) {
  const { screen_id } = use(params)
  const { lastPayload } = useWS()
  const [state, setState] = useState<TVScreenState | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const r = await fetch(`/api/v1/tv/${screen_id}`)
        if (r.ok) setState(await r.json() as TVScreenState)
      } catch { /* network error */ }
    }
    load()
  }, [screen_id, lastPayload])

  if (!state) return (
    <div style={{background:'var(--bg)',minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div className="skeleton" style={{width:400,height:200,borderRadius:16}}/>
    </div>
  )

  const best = state.best_wc
  return (
    <div style={{background:'var(--bg)',minHeight:'100vh',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:40,textAlign:'center'}}>
      <div style={{fontSize:18,color:'var(--text-soft)',marginBottom:8,fontFamily:'DM Mono'}}>
        {state.zone}
      </div>
      <div style={{fontSize:14,color:'var(--text-soft)',marginBottom:32}}>WC recomendada agora</div>

      {best && (
        <div style={{marginBottom:16}}>
          <div className="display-xl" style={{color:occColor(best.status)}}>{best.cluster_id}</div>
          <div style={{fontSize:24,color:'var(--text-soft)',marginTop:4}}>{best.nome}</div>
        </div>
      )}

      {best && (
        <div style={{display:'flex',gap:48,marginBottom:48}}>
          <div style={{textAlign:'center'}}>
            <div className="display" style={{fontSize:'clamp(40px,10vw,64px)'}}>
              {Math.round(best.walk_time_s/60)}<span style={{fontSize:24}}>min</span>
            </div>
            <div style={{fontSize:18,color:'var(--text-soft)'}}>a caminhar</div>
          </div>
          <div style={{textAlign:'center'}}>
            <div className="display" style={{fontSize:'clamp(40px,10vw,64px)'}}>
              {Math.round(best.queue_wait_s/60)}<span style={{fontSize:24}}>min</span>
            </div>
            <div style={{fontSize:18,color:'var(--text-soft)'}}>de espera</div>
          </div>
        </div>
      )}

      {state.alternatives?.length > 0 && (
        <div style={{display:'flex',gap:24,flexWrap:'wrap',justifyContent:'center',marginBottom:32}}>
          {state.alternatives.map((alt) => (
            <AltCard key={alt.cluster_id} alt={alt} />
          ))}
        </div>
      )}

      {state.avoid?.length > 0 && (
        <div style={{fontSize:16,color:'var(--critical)'}}>
          Evitar: {state.avoid.map(a => a.cluster_id).join(', ')}
        </div>
      )}

      <div style={{marginTop:24,fontSize:13,color:'var(--border)',fontFamily:'DM Mono'}}>
        Atualizado via WS · SIMULADO
      </div>
    </div>
  )
}
