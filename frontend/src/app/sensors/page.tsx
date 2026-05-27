'use client'
import { useState, useEffect } from 'react'
import { useWS } from '@/context/WSContext'
import type { SensorHealth, DeviceStatus } from '@/types/api'

const dot = (s: string) => (({online:'●',degraded:'◐',offline:'○'} as Record<string,string>)[s] || '?')
const dotColor = (s: string) => s==='online' ? 'var(--green-bright)' : s==='degraded' ? 'var(--amber)' : 'var(--offline)'

function DeviceCell({ src }: { src?: DeviceStatus }) {
  const st = src?.status || 'offline'
  return (
    <td style={{padding:'12px'}}>
      <span style={{color:dotColor(st),fontSize:18,marginRight:4}}>{dot(st)}</span>
      <span style={{fontSize:13,color:'var(--text-soft)'}}>{src?.last_seen_s?.toFixed(0) || '—'}s</span>
    </td>
  )
}

export default function SensorsPage() {
  const { status } = useWS()
  const [sensors, setSensors] = useState<SensorHealth[]>([])

  useEffect(() => {
    async function load() {
      try {
        const r = await fetch('/api/v1/sensors')
        if (r.ok) setSensors(await r.json() as SensorHealth[])
      } catch { /* network error */ }
    }
    load()
    const i = setInterval(load, 10000)
    return () => clearInterval(i)
  }, [])

  if (status !== 'live' && sensors.length === 0) {
    return <div style={{padding:24,color:'var(--text-soft)'}}>Sem dados ao vivo — sistema offline</div>
  }

  return (
    <div style={{padding:'16px',maxWidth:1000,margin:'0 auto'}}>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:20}}>
        <h1>Sensores</h1>
        <span className="simulado-badge">SIMULADO</span>
      </div>
      <div style={{overflowX:'auto'}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:15}}>
          <thead>
            <tr style={{borderBottom:'2px solid var(--border)',textAlign:'left'}}>
              {['Cluster','LilyGo','IR Entrada','IR Saída','WiFi Agg','Camera ML','LoRaWAN','Confiança','Problemas'].map(h=>(
                <th key={h} style={{padding:'10px 12px',fontWeight:600,whiteSpace:'nowrap',color:'var(--text-soft)',fontSize:13}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sensors.map((s: SensorHealth) => (
              <tr key={s.cluster_id} style={{
                borderBottom:'1px solid var(--border)',
                background: s.overall_confidence < 50 ? 'rgba(194,90,26,0.04)' : 'transparent'
              }}>
                <td style={{
                  padding:'12px',fontWeight:700,
                  color: s.overall_confidence < 50 ? 'var(--critical)' : 'var(--text)'
                }}>{s.cluster_id}</td>
                <DeviceCell src={s.lilygo} />
                <DeviceCell src={s.ir_entry} />
                <DeviceCell src={s.ir_exit} />
                <DeviceCell src={s.wifi_aggregate} />
                <DeviceCell src={s.camera_ml} />
                <DeviceCell src={s.lorawan} />
                <td style={{padding:'12px'}}>
                  <span className="mono" style={{fontSize:14,color:s.overall_confidence<50?'var(--critical)':s.overall_confidence<75?'var(--amber)':'var(--green-bright)'}}>
                    {(s.overall_confidence||0).toFixed(0)}%
                  </span>
                </td>
                <td style={{padding:'12px',fontSize:13,color:'var(--text-soft)'}}>{(s.issues||[]).join(', ')||'—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sensors.length === 0 && <div style={{textAlign:'center',padding:40,color:'var(--text-soft)'}}>A carregar dados de sensores...</div>}
    </div>
  )
}
