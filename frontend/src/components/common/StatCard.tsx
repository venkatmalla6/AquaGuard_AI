interface Props {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
  sub?: string;
}
export default function StatCard({ label, value, icon, color, sub }: Props) {
  return (
    <div className="glass-card p-4 fade-in">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-medium uppercase tracking-wider" style={{ color: '#64748b' }}>{label}</p>
        {icon && <span style={{ color: color ?? '#00b5d4' }}>{icon}</span>}
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: '#64748b' }}>{sub}</p>}
    </div>
  );
}