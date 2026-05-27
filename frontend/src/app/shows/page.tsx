'use client'
import { useState, useEffect } from 'react'
import { useWS } from '@/context/WSContext'
import type { ShowEntry } from '@/types/api'

const DAYS = [
  { date: '2026-06-20', label: '20 Jun' },
  { date: '2026-06-21', label: '21 Jun' },
  { date: '2026-06-27', label: '27 Jun' },
  { date: '2026-06-28', label: '28 Jun' },
]

export default function ShowsPage() {
  const [day, setDay] = useState(DAYS[0].date)
  const [shows, setShows] = useState<ShowEntry[]>([])
  const { lastPayload } = useWS()

  useEffect(() => {
    async function load() {
      try { const r = await fetch(`/api/v1/shows?date=${day}`); if(r.ok) setShows(await r.json() as ShowEntry[]) } catch {}
    }
    load()
  }, [day])

  const minsToNext = lastPayload?.minutos_para_headliner

  return (
    <div style={{padding:16,maxWidth:700,margin:'0 auto'}}>
      <h1 style={{marginBottom:8}}>Programa</h1>
      {minsToNext != null && (
        <div style={{background:'var(--surface-2)',borderRadius:12,padding:'12px 16px',marginBottom:20,fontSize:16}}>
          ⏱ Próximo headliner em <strong className="mono">{Math.round(minsToNext)}min</strong>
        </div>
      )}
      <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap'}}>
        {DAYS.map(d => (
          <button key={d.date} onClick={() => setDay(d.date)}
            style={{padding:'10px 18px',borderRadius:8,border:'none',cursor:'pointer',fontFamily:'DM Sans,sans-serif',
              fontSize:16,fontWeight:day===d.date?600:400,minHeight:48,
              background:day===d.date?'var(--green-mid)':'var(--surface-2)',
              color:day===d.date?'#fff':'var(--text)'}}>
            {d.label}
          </button>
        ))}
      </div>
      <div style={{display:'flex',flexDirection:'column',gap:10}}>
        {shows.map((s: ShowEntry) => (
          <div key={`${s.artista}-${s.inicio}`} className="card"
            style={{borderLeft:`4px solid ${s.headliner?'var(--gold)':s.activo?'var(--green-bright)':'var(--border)'}`}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
              <div>
                <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:4}}>
                  {s.headliner && <span style={{color:'var(--gold)',fontSize:14,fontWeight:700}}>★ HEADLINER</span>}
                  {s.activo && <span style={{color:'var(--green-bright)',fontSize:13,fontWeight:600}}>▶ A DECORRER</span>}
                </div>
                <div style={{fontWeight:700,fontSize:20}}>{s.artista}</div>
                <div style={{fontSize:14,color:'var(--text-soft)'}}>{s.palco_nome||s.palco}</div>
              </div>
              <div className="mono" style={{textAlign:'right',fontSize:16,color:'var(--text-soft)'}}>
                <div>{s.inicio}</div>
                <div style={{fontSize:13}}>{s.fim}</div>
              </div>
            </div>
          </div>
        ))}
        {shows.length === 0 && <div style={{textAlign:'center',color:'var(--text-soft)',padding:40}}>Sem shows para este dia</div>}
      </div>
    </div>
  )
}
