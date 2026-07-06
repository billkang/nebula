interface Props {
  summary?: string;
  onConfirm: () => void;
  onRevise: () => void;
}

export default function ConfirmCard({ summary, onConfirm, onRevise }: Props) {
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
      <h3 className="font-semibold text-green-800 mb-2">需求范围确认</h3>
      {summary && (
        <div className="mb-3">
          <p className="text-sm font-medium text-green-700">需求摘要：</p>
          <p className="text-sm text-green-600 whitespace-pre-wrap">{summary}</p>
        </div>
      )}
      <div className="flex gap-2 mt-3">
        <button onClick={onConfirm}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm">
          ✅ 确认，开始生成文档
        </button>
        <button onClick={onRevise}
          className="px-4 py-2 border border-green-300 text-green-700 rounded-md hover:bg-green-100 text-sm">
          ✏️ 需要调整
        </button>
      </div>
    </div>
  );
}
