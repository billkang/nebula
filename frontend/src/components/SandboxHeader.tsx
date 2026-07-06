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
    <header className="border-b border-gray-200 bg-white px-4 py-2 flex items-center justify-between">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/projects" className="hover:text-gray-700">项目</Link>
        <span>/</span>
        <Link to={`/projects/${projectId}`} className="hover:text-gray-700 truncate max-w-[120px]">
          {projectName}
        </Link>
        <span>/</span>
        <span className="text-gray-800 font-medium">沙箱</span>
      </div>

      {/* 状态 + 操作按钮 */}
      <div className="flex items-center gap-2">
        {/* 文件统计 */}
        <span className="text-xs text-gray-400 mr-1">
          {fileCount} 个文件
          {modifiedCount > 0 && (
            <span className="text-amber-600 ml-1 font-medium">
              · {modifiedCount} 个已修改
            </span>
          )}
        </span>

        {/* 分隔线 */}
        <div className="w-px h-5 bg-gray-200" />

        <button
          onClick={onSaveAll}
          disabled={disableActions}
          className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 transition-colors"
          title="Ctrl+S"
        >
          💾 保存全部
        </button>

        <button
          onClick={onToggleDiffPanel}
          disabled={disableActions}
          className={`px-2.5 py-1 text-xs font-medium rounded border transition-colors
            ${showDiff
              ? 'bg-blue-50 text-blue-600 border-blue-200'
              : 'text-gray-600 bg-white border-gray-200 hover:bg-gray-50'
            } disabled:opacity-40`}
        >
          {showDiff ? '✕ 关闭对比' : '📊 对比差异'}
        </button>

        <button
          onClick={onShowSnapshots}
          disabled={disableActions}
          className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 transition-colors"
        >
          📸 快照
        </button>

        <button
          onClick={onRestoreAll}
          disabled={disableActions || modifiedCount === 0}
          className="px-2.5 py-1 text-xs font-medium text-red-600 bg-white border border-red-200 rounded hover:bg-red-50 disabled:opacity-40 transition-colors"
        >
          ↩️ 恢复原始
        </button>

        {/* 分隔线 */}
        <div className="w-px h-5 bg-gray-200" />

        {isBuilding ? (
          <>
            <span className="text-xs text-gray-400 mr-1">
              <span className="inline-block w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin align-middle mr-1" />
              构建中...
            </span>
            <button
              onClick={onCancelRebuild}
              className="px-2.5 py-1 text-xs font-medium text-red-600 bg-white border border-red-200 rounded hover:bg-red-50 transition-colors"
            >
              ✕ 取消构建
            </button>
          </>
        ) : (
          <button
            onClick={onRebuild}
            className="px-3 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1 bg-purple-600 text-white hover:bg-purple-700"
          >
            🔄 重新构建
          </button>
        )}
      </div>
    </header>
  );
}
