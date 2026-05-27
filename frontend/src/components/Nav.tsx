'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { useWS } from '@/context/WSContext'

const links = [
  { href: '/app', label: 'Rota' },
  { href: '/twin', label: 'Mapa' },
  { href: '/occupation', label: 'WCs' },
  { href: '/sensors', label: 'Sensores' },
  { href: '/shows', label: 'Shows' },
  { href: '/chat', label: 'Chat' },
  { href: '/ops', label: 'Ops' },
]

export default function Nav() {
  const pathname = usePathname()
  const { status } = useWS()
  const [open, setOpen] = useState(false)
  const isTv = pathname.startsWith('/tv/')

  if (isTv) return null

  const pill =
    status === 'live' ? <span className="status-pill status-live">● LIVE</span> :
    status === 'reconnecting' ? <span className="status-pill status-reconnecting">● RECONECTANDO</span> :
    <span className="status-pill status-offline">○ OFFLINE</span>

  return (
    <nav className="nav">
      <Link href="/app" style={{fontFamily:'Cormorant Garamond,serif',fontSize:'20px',fontWeight:600,color:'var(--text)',textDecoration:'none'}}>
        PlantaOS
      </Link>
      <div className="nav-links">
        {links.map(l => (
          <Link key={l.href} href={l.href} className={`nav-link${pathname===l.href?' active':''}`}>{l.label}</Link>
        ))}
      </div>
      {pill}
      <button className="nav-mobile-menu btn btn-secondary" style={{minHeight:40,padding:'0 12px',fontSize:15}} onClick={() => setOpen(!open)}>
        {open ? '✕' : '☰'}
      </button>
      {open && (
        <div style={{position:'absolute',top:56,left:0,right:0,background:'var(--surface)',borderBottom:'1px solid var(--border)',padding:'8px 16px',display:'flex',flexDirection:'column',gap:4,zIndex:99}}>
          {links.map(l => (
            <Link key={l.href} href={l.href} className="nav-link" onClick={() => setOpen(false)}>{l.label}</Link>
          ))}
        </div>
      )}
    </nav>
  )
}
