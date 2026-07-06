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
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* 标题 */}
      <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-200 flex items-center justify-between">
        <span>📸 快照</span>
        <span className="text-gray-400 font-normal">{snapshots.length} 个</span>
      </div>

      {/* 创建新快照 */}
      <div className="px-3 py-2 border-b border-gray-100">
        <div className="flex gap-1">
          <input
            type="text"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="快照描述（选填）"
            className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-blue-300"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
          <button
            onClick={handleCreate}
            disabled={loading}
            className="px-2 py-1 text-xs bg-blue-50 text-blue-600 border border-blue-200 rounded hover:bg-blue-100 disabled:opacity-40 transition-colors whitespace-nowrap"
          >
            + 创建
          </button>
        </div>
      </div>

      {/* 快照列表 */}
      <div className="flex-1 overflow-auto">
        {snapshots.length === 0 ? (
          <div className="px-3 py-4 text-xs text-gray-400 text-center">
            暂无快照
          </div>
        ) : (
          snapshots.map((s) => (
            <div key={s.snapshot_id} className="px-3 py-2 border-b border-gray-50 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-700 truncate">
                    {s.description || `快照 ${s.snapshot_id}`}
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">
                    {s.snapshot_id.replace('_', ' ')}
                    {s.file_count !== undefined && ` · ${s.file_count} 文件`}
                  </div>
                </div>
                <button
                  onClick={() => onRestore(s.snapshot_id)}
                  className="px-1.5 py-0.5 text-[10px] text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors whitespace-nowrap ml-1"
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
