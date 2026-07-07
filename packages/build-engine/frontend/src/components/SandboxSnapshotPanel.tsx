import { useState } from 'react';

interface SnapshotMeta {
  snapshot_id: string;
  created_at: string;
  description: string;
  file_count?: number;
}

interface Props {
  snapshots: SnapshotMeta[];
  onRestore: (id: string) => void;
  onCreate: (description?: string) => void;
  loading: boolean;
}

export default function SandboxSnapshotPanel({ snapshots, onRestore, onCreate, loading }: Props) {
  const [desc, setDesc] = useState('');

  const handleCreate = () => {
    onCreate(desc || undefined);
    setDesc('');
  };

  return (
    <div
      className="flex h-full flex-col border-l"
      style={{
        background: 'var(--color-bg-container)',
        borderColor: 'var(--color-border)',
      }}
    >
      {/* 标题 */}
      <div
        className="flex items-center justify-between border-b px-3 py-2 text-xs font-semibold uppercase tracking-wider"
        style={{
          color: 'var(--color-text-secondary)',
          borderColor: 'var(--color-border)',
        }}
      >
        <span>📸 快照</span>
        <span className="font-normal" style={{ color: 'var(--color-text-secondary)' }}>{snapshots.length} 个</span>
      </div>

      {/* 创建新快照 */}
      <div className="border-b px-3 py-2" style={{ borderColor: 'var(--color-border-secondary)' }}>
        <div className="flex gap-1">
          <input
            type="text"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="快照描述（选填）"
            className="flex-1 rounded border px-2 py-1 text-xs outline-none transition-all duration-150"
            style={{
              borderColor: 'var(--color-border)',
              color: 'var(--color-text-base)',
              background: 'var(--color-bg-layout)',
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
          <button
            onClick={handleCreate}
            disabled={loading}
            className="whitespace-nowrap rounded border px-2 py-1 text-xs transition-colors duration-150 disabled:opacity-40"
            style={{
              color: 'var(--color-primary)',
              background: 'var(--color-primary-bg)',
              borderColor: 'var(--color-primary)',
            }}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = 'rgba(74, 158, 255, 0.15)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-primary-bg)'; }}
          >
            + 创建
          </button>
        </div>
      </div>

      {/* 快照列表 */}
      <div className="flex-1 overflow-auto">
        {snapshots.length === 0 ? (
          <div className="px-3 py-4 text-center text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            暂无快照
          </div>
        ) : (
          snapshots.map((s) => (
            <div
              key={s.snapshot_id}
              className="border-b px-3 py-2 transition-colors duration-150"
              style={{
                borderColor: 'var(--color-border-secondary)',
                background: 'transparent',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-bg-layout)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
            >
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-xs" style={{ color: 'var(--color-text-base)' }}>
                    {s.description || `快照 ${s.snapshot_id}`}
                  </div>
                  <div className="mt-0.5 text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>
                    {s.snapshot_id.replace('_', ' ')}
                    {s.file_count !== undefined && ` · ${s.file_count} 文件`}
                  </div>
                </div>
                <button
                  onClick={() => onRestore(s.snapshot_id)}
                  className="ml-1 whitespace-nowrap rounded px-1.5 py-0.5 text-[10px] transition-colors duration-150"
                  style={{
                    color: 'var(--color-error)',
                    background: 'transparent',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = 'var(--color-error)';
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.06)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = 'var(--color-error)';
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  恢复
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
