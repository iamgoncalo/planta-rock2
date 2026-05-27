'use client'
interface GaugeProps { value: number; max?: number; label: string; size?: number }
export default function Gauge({ value, max = 100, label, size = 120 }: GaugeProps) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  const r = 44; const cx = size/2; const cy = size/2
  const color = pct >= 90 ? '#C25A1A' : pct >= 75 ? '#D48B3A' : pct >= 50 ? '#D4A82A' : '#6FAF82'
  const startAngle = 135; const sweep = 270
  const toRad = (d: number) => (d * Math.PI) / 180
  const sx = cx + r * Math.cos(toRad(startAngle))
  const sy = cy + r * Math.sin(toRad(startAngle))
  const ex = cx + r * Math.cos(toRad(startAngle + sweep))
  const ey = cy + r * Math.sin(toRad(startAngle + sweep))
  const la = sweep > 180 ? 1 : 0
  const bg = `M ${sx} ${sy} A ${r} ${r} 0 ${la} 1 ${ex} ${ey}`
  const endAngle = startAngle + (sweep * pct / 100)
  const px = cx + r * Math.cos(toRad(endAngle))
  const py = cy + r * Math.sin(toRad(endAngle))
  const fla = (sweep * pct / 100) > 180 ? 1 : 0
  const fg = `M ${sx} ${sy} A ${r} ${r} 0 ${fla} 1 ${px} ${py}`
  return (
    <div className="gauge-container">
      <svg width={size} height={size} className="gauge-arc">
        <path d={bg} fill="none" stroke="var(--border)" strokeWidth="10" strokeLinecap="round" />
        {pct > 0 && <path d={fg} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round" />}
        <text x={cx} y={cy+4} textAnchor="middle" fontSize={size*0.22} fill="var(--text)" fontFamily="DM Mono,monospace" fontWeight="500">{Math.round(pct)}%</text>
      </svg>
      <span className="gauge-label">{label}</span>
    </div>
  )
}
