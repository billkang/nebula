import { Link } from 'react-router-dom';

interface Props {
  projectName: string;
  projectId: string;
  modifiedCount: number;
  fileCount: number;
  buildStatus: string;
  showDiff: boolean;
  onSaveAll: () => void;
  onViewDiff: () => void;
  onRestoreAll: () => void;
  onRebuild: () => void;
  onCancelRebuild: () => void;
  onShowSnapshots: () => void;
  onToggleDiffPanel: () => void;
}

export default function SandboxHeader({
  projectName,
  projectId,
  modifiedCount,
  fileCount,
  buildStatus,
  showDiff,
  onSaveAll,
  onViewDiff,
  onRestoreAll,
  onRebuild,
  onCancelRebuild,
  onShowSnapshots,
  onToggleDiffPanel,
}: Props) {
  const isBuilding = buildStatus === 'running';
  const disableActions = isBuilding;

  return (
    <header
      className="flex items-center justify-between border-b px-4 py-2"
      style={{
        borderColor: 'var(--color-border)',
        background: 'var(--color-bg-container)',
      }}
    >
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
        <Link
          to="/projects"
          className="transition-colors duration-150"
          style={{ color: 'var(--color-text-secondary)' }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-text-base)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-text-secondary)'; }}
        >
          项目
        </Link>
        <span>/</span>
        <Link
          to={`/projects/${projectId}`}
          className="max-w-[120px] truncate transition-colors duration-150"
          style={{ color: 'var(--color-text-secondary)' }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-text-base)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-text-secondary)'; }}
        >
          {projectName}
        </Link>
        <span>/</span>
        <span className="font-medium" style={{ color: 'var(--color-text-base)' }}>沙箱</span>
      </div>

      {/* 状态 + 操作按钮 */}
      <div className="flex items-center gap-2">
        {/* 文件统计 */}
        <span className="mr-1 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          {fileCount} 个文件
          {modifiedCount > 0 && (
            <span className="ml-1 font-medium" style={{ color: 'var(--color-warning)' }}>
              · {modifiedCount} 个已修改
            </span>
          )}
        </span>

        {/* 分隔线 */}
        <div className="h-5 w-px" style={{ background: 'var(--color-border)' }} />

        <button
          onClick={onSaveAll}
          disabled={disableActions}
          className="rounded border px-2.5 py-1 text-xs font-medium transition-colors duration-150 disabled:opacity-40"
          style={{
            color: 'var(--color-text-base)',
            background: 'var(--color-bg-container)',
            borderColor: 'var(--color-border)',
          }}
          onMouseEnter={(e) => { if (!disableActions) e.currentTarget.style.background = 'var(--color-bg-layout)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-bg-container)'; }}
          title="Ctrl+S"
        >
          💾 保存全部
        </button>

        <button
          onClick={onToggleDiffPanel}
          disabled={disableActions}
          className="rounded border px-2.5 py-1 text-xs font-medium transition-colors duration-150 disabled:opacity-40"
          style={{
            color: showDiff ? 'var(--color-primary)' : 'var(--color-text-base)',
            background: showDiff ? 'var(--color-primary-bg)' : 'var(--color-bg-container)',
            borderColor: showDiff ? 'var(--color-primary)' : 'var(--color-border)',
          }}
          onMouseEnter={(e) => {
            if (!disableActions && !showDiff)
              e.currentTarget.style.background = 'var(--color-bg-layout)';
          }}
          onMouseLeave={(e) => {
            if (!showDiff)
              e.currentTarget.style.background = 'var(--color-bg-container)';
          }}
        >
          {showDiff ? '✕ 关闭对比' : '📊 对比差异'}
        </button>

        <button
          onClick={onShowSnapshots}
          disabled={disableActions}
          className="rounded border px-2.5 py-1 text-xs font-medium transition-colors duration-150 disabled:opacity-40"
          style={{
            color: 'var(--color-text-base)',
            background: 'var(--color-bg-container)',
            borderColor: 'var(--color-border)',
          }}
          onMouseEnter={(e) => { if (!disableActions) e.currentTarget.style.background = 'var(--color-bg-layout)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-bg-container)'; }}
        >
          📸 快照
        </button>

        <button
          onClick={onRestoreAll}
          disabled={disableActions || modifiedCount === 0}
          className="rounded border px-2.5 py-1 text-xs font-medium transition-colors duration-150 disabled:opacity-40"
          style={{
            color: 'var(--color-error)',
            background: 'var(--color-bg-container)',
            borderColor: 'rgba(239, 68, 68, 0.2)',
          }}
          onMouseEnter={(e) => { if (!disableActions && modifiedCount > 0) e.currentTarget.style.background = 'rgba(239, 68, 68, 0.06)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-bg-container)'; }}
        >
          ↩️ 恢复原始
        </button>

        {/* 分隔线 */}
        <div className="h-5 w-px" style={{ background: 'var(--color-border)' }} />

        {isBuilding ? (
          <>
            <span className="mr-1 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              <span
                className="mr-1 inline-block h-3 w-3 animate-spin rounded-full border-2 align-middle"
                style={{
                  borderColor: 'var(--color-primary)',
                  borderTopColor: 'transparent',
                }}
              />
              构建中...
            </span>
            <button
              onClick={onCancelRebuild}
              className="rounded border px-2.5 py-1 text-xs font-medium transition-colors duration-150"
              style={{
                color: 'var(--color-error)',
                background: 'var(--color-bg-container)',
                borderColor: 'rgba(239, 68, 68, 0.2)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.06)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-bg-container)'; }}
            >
              ✕ 取消构建
            </button>
          </>
        ) : (
          <button
            onClick={onRebuild}
            className="flex items-center gap-1 rounded px-3 py-1 text-xs font-medium text-white transition-colors duration-150"
            style={{ background: 'var(--color-primary)' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-primary-hover)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-primary)'; }}
          >
            🔄 重新构建
          </button>
        )}
      </div>
    </header>
  );
}
