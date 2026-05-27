'use client'
import { useState, useRef, useEffect } from 'react'
import { useWS } from '@/context/WSContext'

const CHIPS = [
  'Qual a WC com menos fila?',
  'Quanto tempo demoro à WC-06?',
  'Há WC acessível livre?',
  'Quando acaba o headliner?',
]

interface Msg { role: 'user'|'assistant'; content: string }

export default function ChatPage() {
  const { kpis, lastPayload } = useWS()
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const nextHL = lastPayload?.minutos_para_headliner
  const showActivo = lastPayload?.show_activo

  useEffect(() => { bottomRef.current?.scrollIntoView({behavior:'smooth'}) }, [msgs])

  async function send(text: string) {
    if (!text.trim() || loading) return
    const msg = text.trim()
    setInput('')
    setMsgs(m => [...m, {role:'user',content:msg}])
    setLoading(true)
    try {
      const r = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ mensagem: msg, historico: msgs.slice(-6).map(m=>({role:m.role,content:m.content})) })
      })
      const d = await r.json()
      setMsgs(m => [...m, {role:'assistant',content:d.resposta||'Dados não disponíveis.'}])
    } catch {
      setMsgs(m => [...m, {role:'assistant',content:'Backend indisponível, tente novamente em 5s.'}])
    }
    setLoading(false)
  }

  return (
    <div style={{maxWidth:680,margin:'0 auto',display:'flex',flexDirection:'column',height:'calc(100vh - 56px)'}}>
      {/* Context bar */}
      <div style={{padding:'10px 16px',background:'var(--surface-2)',borderBottom:'1px solid var(--border)',fontSize:14,color:'var(--text-soft)',flexShrink:0}}>
        {nextHL!=null ? `⏱ Próximo headliner em ${Math.round(nextHL)}min` : showActivo ? `▶ A decorrer: ${showActivo}` : '● Rock in Rio Lisboa 2026 · 8 clusters'}
        {kpis && <span style={{marginLeft:12,fontFamily:'DM Mono',fontSize:13}}>util. média: {(kpis.kpi_02||0).toFixed(0)}%</span>}
        <span className="simulado-badge" style={{marginLeft:12}}>SIMULADO</span>
      </div>

      {/* Messages */}
      <div style={{flex:1,overflowY:'auto',padding:16,display:'flex',flexDirection:'column',gap:12}}>
        {msgs.length === 0 && (
          <div style={{textAlign:'center',color:'var(--text-soft)',padding:'40px 0'}}>
            <div style={{fontSize:40,marginBottom:12}}>🚽</div>
            <div style={{fontSize:16}}>Pergunta-me sobre as WCs — respondo com dados ao vivo.</div>
          </div>
        )}
        {msgs.map((m,i) => (
          <div key={i} style={{display:'flex',justifyContent:m.role==='user'?'flex-end':'flex-start'}}>
            <div style={{
              maxWidth:'80%',padding:'12px 16px',borderRadius:m.role==='user'?'16px 16px 4px 16px':'16px 16px 16px 4px',
              background:m.role==='user'?'var(--green-mid)':'var(--surface)',
              color:m.role==='user'?'#fff':'var(--text)',
              border:m.role==='assistant'?'1px solid var(--border)':'none',
              fontSize:16,lineHeight:1.5,
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{display:'flex'}}>
            <div className="skeleton" style={{width:80,height:40,borderRadius:16}}/>
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Chips */}
      {msgs.length === 0 && (
        <div style={{padding:'0 16px 12px',display:'flex',gap:8,flexWrap:'wrap',flexShrink:0}}>
          {CHIPS.map(c => (
            <button key={c} onClick={() => send(c)}
              style={{padding:'8px 14px',borderRadius:99,border:'1px solid var(--border)',background:'var(--surface)',
                color:'var(--text)',fontSize:14,cursor:'pointer',fontFamily:'DM Sans,sans-serif',minHeight:40}}>
              {c}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{padding:16,borderTop:'1px solid var(--border)',display:'flex',gap:10,flexShrink:0,background:'var(--surface)'}}>
        <textarea value={input} onChange={e=>setInput(e.target.value)}
          onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(input)}}}
          placeholder="Escreve a tua pergunta..."
          style={{flex:1,minHeight:56,maxHeight:120,padding:'12px 14px',borderRadius:10,border:'1px solid var(--border)',
            fontFamily:'DM Sans,sans-serif',fontSize:16,resize:'none',background:'var(--surface)',color:'var(--text)',
            outline:'none'}}
        />
        <button onClick={() => send(input)} disabled={!input.trim()||loading}
          className="btn btn-primary" style={{alignSelf:'flex-end',height:56,opacity:(!input.trim()||loading)?0.5:1}}>
          →
        </button>
      </div>
    </div>
  )
}
