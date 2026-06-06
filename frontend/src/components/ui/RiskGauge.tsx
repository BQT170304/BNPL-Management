interface Props {
  score: number;
  size?: number;
  label?: string;
}

export function RiskGauge({ score, size = 120, label }: Props) {
  const r = (size - 20) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, score));
  const offset = circ - (pct / 100) * circ;

  const color = pct <= 30 ? '#22C55E' : pct <= 60 ? '#F59E0B' : '#EF4444';
  const statusLabel = pct <= 30 ? 'Thấp ✅' : pct <= 60 ? 'Trung bình ⚠️' : 'Cao ❌';
  const textLabel = label ?? statusLabel;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#E2E8F0" strokeWidth={10} />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none" stroke={color} strokeWidth={10}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
        <text
          x={size/2} y={size/2}
          textAnchor="middle" dominantBaseline="central"
          style={{ transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px`, fontFamily: 'Inter', fontWeight: 700 }}
          fill={color} fontSize={size * 0.22}
        >
          {Math.round(pct)}
        </text>
      </svg>
      <span style={{ fontSize: 12, color: '#43474e', fontWeight: 500 }}>{textLabel}</span>
    </div>
  );
}
