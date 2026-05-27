'use client'
import { useState, useEffect } from 'react'
import { useWS } from '@/context/WSContext'
import type { SensorHealth, DeviceStatus } from '@/types/api'

interface LogEntry { ts: number; cluster: string; action: string; notes: string }

const INVENTORY_INIT = [
  { component: 'Reed MC-38', stock: 20, buffer: 10, order_below: 10 },
  { component: 'IR E18-D80NK', stock: 8, buffer: 4, order_below: 4 },
  { component: 'LilyGo T-SIM7000G', stock: 2, buffer: 2, order_below: 2 },
  { component: 'PoE injector', stock: 10, buffer: 4, order_below: 4 },
  { component: 'CAT6 cable (m)', stock: 100, buffer: 50, order_below: 50 },
]

const CHECKLIST = [
  'Todos os 8 LilyGos ligados e online',
  'Todos os 16 pares IR calibrados (alcance 95cm verificado)',
  'Todos os ~160 reed switches instalados e testados',
  'WebSocket a enviar de 5 em 5s durante 1h sem drops',
  'SCOR Sensaway a receber 14 registos/min',
  'Todos os clusters visíveis no mapa /twin',
  'App /app carrega em <2s no telefone de teste',
  'SIM LoRaWAN de backup ligada e registada',
]

export default function ManutencaoPage() {
  const [sensors, setSensors] = useState<SensorHealth[]>([])
  const [log, setLog] = useState<LogEntry[]>([])
  const [checked, setChecked] = useState<boolean[]>(Array(CHECKLIST.length).fill(false))
  useWS()

  useEffect(() => {
    async function load() {
      try {
        const [sr, lr] = await Promise.all([
          fetch('/api/v1/sensors'), fetch('/api/v1/maintenance/log')
        ])
        if (sr.ok) setSensors(await sr.json() as SensorHealth[])
        if (lr.ok) setLog(await lr.json() as LogEntry[])
      } catch { /* network error */ }
    }
    load()
    const i = setInterval(load, 30000)
    return () => clearInterval(i)
  }, [])

  function dotColor(d: DeviceStatus | undefined) { return d?.status==='online'?'var(--green-bright)':d?.status==='degraded'?'var(--amber)':'var(--offline)' }
  function dot(d: DeviceStatus | undefined) { return d?.status==='online'?'●':d?.status==='degraded'?'◐':'○' }

  return (
    <div style={{padding:16,maxWidth:900,margin:'0 auto'}}>
      <h1 style={{marginBottom:20}}>Manutenção</h1>

      {/* Sensor health */}
      <div className="card" style={{marginBottom:20}}>
        <h2 style={{marginBottom:12}}>Saúde dos Sensores <span className="simulado-badge" style={{fontSize:11}}>SIMULADO</span></h2>
        <div style={{overflowX:'auto'}}>
          <table style={{width:'100%',borderCollapse:'collapse',fontSize:14}}>
            <thead>
              <tr style={{borderBottom:'2px solid var(--border)'}}>
                {['Cluster','LilyGo','IR Entry','IR Exit','WiFi','Camera','Confiança'].map(h=>(
                  <th key={h} style={{padding:'8px 10px',fontWeight:600,textAlign:'left',color:'var(--text-soft)',fontSize:13}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sensors.map((s: SensorHealth)=>{
                const srcs: (DeviceStatus | undefined)[] = [s.lilygo,s.ir_entry,s.ir_exit,s.wifi_aggregate,s.camera_ml]
                return (
                  <tr key={s.cluster_id} style={{borderBottom:'1px solid var(--border)'}}>
                    <td style={{padding:'10px',fontWeight:700}}>{s.cluster_id}</td>
                    {srcs.map((src,i)=>(
                      <td key={i} style={{padding:'10px'}}>
                        <span style={{color:dotColor(src)}}>{dot(src)}</span>
                      </td>
                    ))}
                    <td style={{padding:'10px'}} className="mono">{(s.overall_confidence||0).toFixed(0)}%</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Readiness checklist */}
      <div className="card" style={{marginBottom:20}}>
        <h2 style={{marginBottom:12}}>Checklist Pré-Festival (11–12 Jun 2026)</h2>
        {CHECKLIST.map((item,i)=>(
          <label key={i} style={{display:'flex',alignItems:'flex-start',gap:12,padding:'10px 0',borderBottom:'1px solid var(--border)',cursor:'pointer',fontSize:15}}>
            <input type="checkbox" checked={checked[i]} onChange={()=>setChecked(c=>{const n=[...c];n[i]=!n[i];return n})}
              style={{width:20,height:20,marginTop:2,accentColor:'var(--green-mid)',flexShrink:0}}/>
            <span style={{color:checked[i]?'var(--text-soft)':'var(--text)',textDecoration:checked[i]?'line-through':'none'}}>{item}</span>
          </label>
        ))}
        <div style={{marginTop:12,fontSize:14,color:'var(--text-soft)'}}>{checked.filter(Boolean).length}/{CHECKLIST.length} itens concluídos</div>
      </div>

      {/* Inventory */}
      <div className="card" style={{marginBottom:20}}>
        <h2 style={{marginBottom:12}}>Inventário</h2>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:15}}>
          <thead>
            <tr style={{borderBottom:'2px solid var(--border)'}}>
              {['Componente','Stock','Buffer','Encomendar se <'].map(h=>(
                <th key={h} style={{padding:'8px 12px',textAlign:'left',color:'var(--text-soft)',fontSize:13,fontWeight:600}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {INVENTORY_INIT.map(row=>(
              <tr key={row.component} style={{borderBottom:'1px solid var(--border)'}}>
                <td style={{padding:'10px 12px',fontWeight:500}}>{row.component}</td>
                <td style={{padding:'10px 12px'}} className="mono">
                  <span style={{color:row.stock<=row.order_below?'var(--critical)':'var(--text)',fontWeight:row.stock<=row.order_below?700:400}}>{row.stock}</span>
                </td>
                <td style={{padding:'10px 12px'}} className="mono">{row.buffer}</td>
                <td style={{padding:'10px 12px'}} className="mono">{row.order_below}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Log */}
      <div className="card">
        <h2 style={{marginBottom:12}}>Log de Instalação</h2>
        {log.length === 0 ? <p style={{color:'var(--text-soft)'}}>Sem registos.</p> : (
          <div style={{display:'flex',flexDirection:'column',gap:6}}>
            {[...log].reverse().map((entry: LogEntry, i: number)=>(
              <div key={i} style={{padding:'8px 12px',background:'var(--surface-2)',borderRadius:6,fontSize:14}}>
                <span className="mono" style={{color:'var(--text-soft)',marginRight:8}}>{new Date(entry.ts*1000).toLocaleString('pt-PT')}</span>
                <strong>{entry.cluster}</strong> · {entry.action} · {entry.notes}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
