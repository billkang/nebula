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
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-sm text-gray-400">加载 diff 中...</div>
      </div>
    );
  }

  if (!diff) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center text-sm text-gray-400">
          <div className="text-2xl mb-2">📊</div>
          <p>选择一个已修改的文件查看 diff</p>
        </div>
      </div>
    );
  }

  if (!diff.has_diff) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center text-sm text-green-600">
          <div className="text-2xl mb-2">✅</div>
          <p>{diff.path}</p>
          <p className="text-gray-500">此文件无修改</p>
        </div>
      </div>
    );
  }

  // 渲染 unified diff
  const lines = diff.diff.split('\n');

  return (
    <div className="h-full overflow-auto bg-white">
      {/* header */}
      <div className="px-4 py-2 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="text-sm font-medium text-gray-700 truncate">{diff.path}</div>
        <div className="text-xs text-gray-500">
          <span className="text-green-600">+{diff.additions}</span>
          {' / '}
          <span className="text-red-600">-{diff.removals}</span>
          {' 行变更'}
        </div>
      </div>

      {/* diff 行 */}
      <div className="font-mono text-xs leading-relaxed">
        {lines.map((line, i) => {
          if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('@@')) {
            return (
              <div key={i} className="px-4 py-0.5 bg-blue-50 text-blue-600">
                {line}
              </div>
            );
          }
          if (line.startsWith('+')) {
            return (
              <div key={i} className="px-4 py-0.5 bg-green-50 text-green-800">
                <span className="text-green-500 select-none mr-1">+</span>
                {line.slice(1)}
              </div>
            );
          }
          if (line.startsWith('-')) {
            return (
              <div key={i} className="px-4 py-0.5 bg-red-50 text-red-800">
                <span className="text-red-500 select-none mr-1">-</span>
                {line.slice(1)}
              </div>
            );
          }
          return (
            <div key={i} className="px-4 py-0.5 text-gray-600">
              <span className="text-gray-300 select-none mr-1"> </span>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}
