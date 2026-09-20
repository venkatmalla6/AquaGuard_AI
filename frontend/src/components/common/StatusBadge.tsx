import type { BehaviorClass } from '../../types';

const config: Record<BehaviorClass, { label: string; color: string; bg: string; border: string }> = {
  normal:             { label: 'NORMAL',   color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  border: 'rgba(34,197,94,0.3)' },
  distress:           { label: 'DISTRESS', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)' },
  potential_drowning: { label: 'DROWNING', color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.3)' },
  drowning:           { label: 'DROWNING', color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.3)' },
};

interface Props {
  behavior: BehaviorClass;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

export function StatusBadge({ behavior, size = 'md', pulse }: Props) {
  const c = config[behavior];
  const sz = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1';
  const pl = pulse && behavior === 'potential_drowning' ? ' alert-pulse' : '';
  return (
    <span
      className={`inline-flex items-center font-bold rounded tracking-wider ${sz}${pl}`}
      style={{ color: c.color, background: c.bg, border: `1px solid ${c.border}` }}
    >
      {c.label}
    </span>
  );
}

export default StatusBadge;
