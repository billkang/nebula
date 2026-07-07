interface Props {
  summary?: string;
  onConfirm: () => void;
  onRevise: () => void;
}

export default function ConfirmCard({ summary, onConfirm, onRevise }: Props) {
  return (
    <div
      className="mb-4 rounded-xl p-4"
      style={{
        background: 'var(--color-primary-bg)',
        borderLeft: '3px solid var(--color-primary)',
        borderTop: '1px solid var(--color-border)',
        borderRight: '1px solid var(--color-border)',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <h3 className="mb-2 font-semibold" style={{ color: 'var(--color-text-base)' }}>
        需求范围确认
      </h3>
      {summary && (
        <div className="mb-3">
          <p className="text-sm font-medium" style={{ color: 'var(--color-text-base)' }}>
            需求摘要：
          </p>
          <p
            className="mt-1 whitespace-pre-wrap text-sm"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            {summary}
          </p>
        </div>
      )}
      <div className="mt-3 flex gap-2">
        <button
          onClick={onConfirm}
          className="rounded-lg px-4 py-2 text-sm text-white transition-all duration-200 hover:scale-[1.02]"
          style={{ background: 'var(--color-primary)' }}
        >
          ✅ 确认，开始生成文档
        </button>
        <button
          onClick={onRevise}
          className="rounded-lg border px-4 py-2 text-sm transition-all duration-200"
          style={{
            borderColor: 'var(--color-border)',
            color: 'var(--color-text-base)',
            background: 'var(--color-bg-container)',
          }}
        >
          ✏️ 需要调整
        </button>
      </div>
    </div>
  );
}
