interface Props { status: string }

const labels: Record<string, string> = {
  idle: '等待中', running: '执行中', testing: '测试中',
  verifying: '校验中', packaging: '打包中', success: '已完成', failed: '失败',
};

const statusColorMap: Record<string, string> = {
  idle: 'var(--color-text-secondary)',
  running: 'var(--color-primary)',
  testing: 'var(--color-warning)',
  verifying: 'var(--color-warning)',
  packaging: 'var(--color-primary)',
  success: 'var(--color-success)',
  failed: 'var(--color-error)',
};

export default function StatusBadge({ status }: Props) {
  const color = statusColorMap[status] || 'var(--color-text-secondary)';

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{
        background: `${color}15`,
        color,
      }}
    >
      {status === 'running' && (
        <span
          className="inline-block h-1.5 w-1.5 rounded-full"
          style={{
            background: color,
            animation: 'pulse-dot 1.5s ease-in-out infinite',
          }}
        />
      )}
      {labels[status] || status}
    </span>
  );
}
