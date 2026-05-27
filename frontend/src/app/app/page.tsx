'use client'
import { useState, useEffect } from 'react'
import { useWS } from '@/context/WSContext'
import type { RouteOption } from '@/types/api'

const PREFS = [
  { key: 'fastest', label: 'Mais rápida', icon: '⚡' },
  { key: 'least_crowded', label: 'Menos cheia', icon: '🌿' },
  { key: 'safest', label: 'Mais segura', icon: '🛡' },
  { key: 'accessible', label: 'Acessível', icon: '♿' },
]

export default function AppPage() {
  const { status, clusters } = useWS()
  const [pref, setPref] = useState('fastest')
  const [geo, setGeo] = useState<{lat:number,lon:number}|null>(null)
  const [geoError, setGeoError] = useState<string|null>(null)
  const [options, setOptions] = useState<RouteOption[]>([])
  const [loading, setLoading] = useState(false)
  const offline = status !== 'live'

  function requestGeo() {
    if (!navigator.geolocation) { setGeoError('Geolocalização não disponível'); return }
    navigator.geolocation.getCurrentPosition(
      p => setGeo({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => {
        // festival venue center as fallback
        setGeo({ lat: 38.78111, lon: -9.09310 })
      }
    )
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (geo) fetchRoute() }, [geo, pref, clusters])

  async function fetchRoute() {
    if (!geo || offline) return
    setLoading(true)
    try {
      const r = await fetch('/api/v1/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: geo.lat, lon: geo.lon, preference: pref })
      })
      if (r.ok) {
        const d = await r.json() as { options?: RouteOption[] }
        setOptions(d.options || [])
      }
    } catch { /* network error */ }
    setLoading(false)
  }

  const statusColor = status === 'live' ? 'var(--green-mid)' : status === 'reconnecting' ? 'var(--amber)' : 'var(--offline)'

  return (
    <div style={{maxWidth:480,margin:'0 auto',padding:'16px 16px 80px'}}>
      {/* Status + SimBadge */}
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:16}}>
        <span style={{fontSize:14,color:'var(--text-soft)'}}>Rock in Rio Lisboa 2026</span>
        <div style={{display:'flex',gap:8,alignItems:'center'}}>
          <span style={{display:'inline-flex',alignItems:'center',gap:5,padding:'3px 10px',borderRadius:99,background:'var(--surface-2)',fontSize:13,fontWeight:500}}>
            <span style={{width:8,height:8,borderRadius:'50%',background:statusColor,display:'inline-block'}}></span>
            {status === 'live' ? 'LIVE' : status === 'reconnecting' ? 'RECONECTANDO' : 'OFFLINE'}
          </span>
          <span className="simulado-badge">SIMULADO</span>
        </div>
      </div>

      <h1 style={{marginBottom:8}}>Encontra a tua WC</h1>
      <p style={{fontSize:16,color:'var(--text-soft)',marginBottom:24}}>
        A mais rápida, mais livre, mais próxima — agora.
      </p>

      {/* Offline banner */}
      {offline && (
        <div style={{background:'#FFF3E0',border:'1px solid var(--amber)',borderRadius:'12px',padding:'12px 16px',marginBottom:24,color:'#7C4000',fontWeight:500}}>
          Sem dados ao vivo — sistema offline
        </div>
      )}

      {/* Geo permission */}
      {!geo && !offline && (
        <div className="card" style={{marginBottom:24,textAlign:'center',padding:32}}>
          <div style={{fontSize:48,marginBottom:12}}>📍</div>
          <p style={{fontSize:16,color:'var(--text-soft)',marginBottom:20}}>
            A Planta Rock in Rio precisa da tua localização para te indicar a WC mais próxima. Não guardamos a tua posição.
          </p>
          <button className="btn btn-primary" style={{width:'100%'}} onClick={requestGeo}>
            Permitir localização
          </button>
          {geoError && <p style={{color:'var(--critical)',marginTop:8,fontSize:14}}>{geoError}</p>}
        </div>
      )}

      {/* Preference chips */}
      {geo && (
        <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:24}}>
          {PREFS.map(p => (
            <button key={p.key} onClick={() => setPref(p.key)}
              style={{padding:'10px 16px',borderRadius:99,border:`2px solid ${pref===p.key?'var(--green-mid)':'var(--border)'}`,
                background:pref===p.key?'var(--green-mid)':'var(--surface)',
                color:pref===p.key?'#fff':'var(--text)',
                fontFamily:'DM Sans,sans-serif',fontSize:15,fontWeight:500,cursor:'pointer',
                minHeight:48,transition:'all 0.15s'}}>
              {p.icon} {p.label}
            </button>
          ))}
        </div>
      )}

      {/* Loading skeletons */}
      {loading && (
        <div style={{display:'flex',flexDirection:'column',gap:12}}>
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{height:120,borderRadius:12}} />)}
        </div>
      )}

      {/* Route options */}
      {!loading && options.length > 0 && (
        <div style={{display:'flex',flexDirection:'column',gap:12}}>
          {options.map((opt, i) => (
            <div key={opt.cluster_id} className="card" style={{
              border: i===0 ? '2px solid var(--green-mid)' : '1px solid var(--border)',
              position:'relative', overflow:'hidden'
            }}>
              {i===0 && <div style={{position:'absolute',top:0,left:0,right:0,height:3,background:'var(--green-mid)'}} />}
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                <div>
                  {i===0 && <span style={{fontSize:11,fontWeight:700,color:'var(--green-mid)',letterSpacing:'0.08em'}}>MELHOR OPÇÃO</span>}
                  <h3 style={{fontSize:22,marginTop:i===0?2:0}}>{opt.nome || opt.cluster_id}</h3>
                </div>
                <span className="display" style={{fontSize:'clamp(40px,10vw,56px)',color:i===0?'var(--green-mid)':'var(--text)'}}>
                  {opt.total_cost_min.toFixed(0)}<span style={{fontSize:18}}>min</span>
                </span>
              </div>
              <div style={{display:'flex',gap:16,fontSize:15,color:'var(--text-soft)',marginBottom:12}}>
                <span>🚶 {opt.walk_time_min.toFixed(1)}min</span>
                <span>⏳ {opt.queue_wait_min.toFixed(1)}min fila</span>
              </div>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <span style={{fontSize:14,color:'var(--text-soft)'}}>{opt.reason}</span>
                <a href={`/occupation#${opt.cluster_id}`}
                  style={{display:'inline-flex',alignItems:'center',justifyContent:'center',
                    minHeight:48,minWidth:80,padding:'0 16px',borderRadius:8,
                    background:'var(--green-mid)',color:'#fff',fontWeight:600,
                    textDecoration:'none',fontSize:16}}>
                  Ir →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && geo && options.length === 0 && !offline && (
        <div className="card" style={{textAlign:'center',padding:40}}>
          <div style={{fontSize:40,marginBottom:12}}>🔄</div>
          <p style={{color:'var(--text-soft)'}}>A carregar dados em tempo real...</p>
        </div>
      )}
    </div>
  )
}
