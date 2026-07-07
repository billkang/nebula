interface DiffResult {
  path: string;
  has_diff: boolean;
  diff: string;
  summary: string;
  additions?: number;
  removals?: number;
}

interface Props {
  diff: DiffResult | null;
  loading: boolean;
}

export default function SandboxDiffView({ diff, loading }: Props) {
  if (loading) {
    return (
      <div
        className="flex h-full items-center justify-center"
        style={{ background: 'var(--color-bg-layout)' }}
      >
        <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>加载 diff 中...</div>
      </div>
    );
  }

  if (!diff) {
    return (
      <div
        className="flex h-full items-center justify-center"
        style={{ background: 'var(--color-bg-layout)' }}
      >
        <div className="text-center text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          <div className="mb-2 text-2xl">📊</div>
          <p>选择一个已修改的文件查看 diff</p>
        </div>
      </div>
    );
  }

  if (!diff.has_diff) {
    return (
      <div
        className="flex h-full items-center justify-center"
        style={{ background: 'var(--color-bg-layout)' }}
      >
        <div className="text-center text-sm" style={{ color: 'var(--color-success)' }}>
          <div className="mb-2 text-2xl">✅</div>
          <p>{diff.path}</p>
          <p style={{ color: 'var(--color-text-secondary)' }}>此文件无修改</p>
        </div>
      </div>
    );
  }

  // 渲染 unified diff
  const lines = diff.diff.split('\n');

  return (
    <div className="h-full overflow-auto" style={{ background: 'var(--color-bg-container)' }}>
      {/* header */}
      <div
        className="flex items-center justify-between border-b px-4 py-2"
        style={{
          borderColor: 'var(--color-border)',
          background: 'var(--color-bg-layout)',
        }}
      >
        <div className="truncate text-sm font-medium" style={{ color: 'var(--color-text-base)' }}>{diff.path}</div>
        <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          <span style={{ color: 'var(--color-success)' }}>+{diff.additions}</span>
          {' / '}
          <span style={{ color: 'var(--color-error)' }}>-{diff.removals}</span>
          {' 行变更'}
        </div>
      </div>

      {/* diff 行 */}
      <div className="font-mono text-xs leading-relaxed">
        {lines.map((line, i) => {
          if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('@@')) {
            return (
              <div
                key={i}
                className="px-4 py-0.5"
                style={{
                  background: 'rgba(74, 158, 255, 0.06)',
                  color: 'var(--color-primary)',
                }}
              >
                {line}
              </div>
            );
          }
          if (line.startsWith('+')) {
            return (
              <div
                key={i}
                className="px-4 py-0.5"
                style={{
                  background: 'rgba(34, 197, 94, 0.06)',
                  color: 'var(--color-success)',
                }}
              >
                <span className="mr-1 select-none" style={{ color: 'var(--color-success)' }}>+</span>
                {line.slice(1)}
              </div>
            );
          }
          if (line.startsWith('-')) {
            return (
              <div
                key={i}
                className="px-4 py-0.5"
                style={{
                  background: 'rgba(239, 68, 68, 0.06)',
                  color: 'var(--color-error)',
                }}
              >
                <span className="mr-1 select-none" style={{ color: 'var(--color-error)' }}>-</span>
                {line.slice(1)}
              </div>
            );
          }
          return (
            <div key={i} className="px-4 py-0.5" style={{ color: 'var(--color-text-secondary)' }}>
              <span className="mr-1 select-none" style={{ color: 'var(--color-border)' }}> </span>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}
