'use client'
import { useWS } from '@/context/WSContext'
export default function StatusPill() {
  const { status } = useWS()
  if (status === 'live') return <span className="status-pill status-live">● LIVE</span>
  if (status === 'reconnecting') return <span className="status-pill status-reconnecting">● RECONECTANDO</span>
  return <span className="status-pill status-offline">○ OFFLINE</span>
}
