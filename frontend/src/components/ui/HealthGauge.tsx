interface Props {
  score: number;
  size?: number;
}

export function HealthGauge({ score, size = 140 }: Props) {
  const r = (size - 20) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, score));
  const offset = circ - (pct / 100) * circ;

  const color = pct >= 70 ? '#22C55E' : pct >= 40 ? '#F59E0B' : '#EF4444';
  const label = pct >= 70 ? 'Kha tot ✓' : pct >= 40 ? 'Trung binh' : 'Can cai thien';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#E2E8F0" strokeWidth={12} />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none" stroke={color} strokeWidth={12}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        <text
          x={size/2} y={size/2 - 6}
          textAnchor="middle" dominantBaseline="central"
          style={{ transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px`, fontFamily: 'Inter', fontWeight: 700 }}
          fill={color} fontSize={size * 0.22}
        >
          {Math.round(pct)}
        </text>
        <text
          x={size/2} y={size/2 + size*0.14}
          textAnchor="middle" dominantBaseline="central"
          style={{ transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px`, fontFamily: 'Inter' }}
          fill="#74777f" fontSize={size * 0.1}
        >
          /100
        </text>
      </svg>
      <span style={{ fontSize: 13, color, fontWeight: 600 }}>{label}</span>
    </div>
  );
}
