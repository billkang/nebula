interface Props { status: string }

const conf: Record<string, [string, string]> = {
  idle: ['bg-gray-100', 'text-gray-600'], running: ['bg-blue-100', 'text-blue-600'],
  testing: ['bg-yellow-100', 'text-yellow-600'], verifying: ['bg-yellow-100', 'text-yellow-600'],
  packaging: ['bg-purple-100', 'text-purple-600'], success: ['bg-green-100', 'text-green-600'],
  failed: ['bg-red-100', 'text-red-600'],
};
const labels: Record<string, string> = {
  idle: '等待中', running: '执行中', testing: '测试中',
  verifying: '校验中', packaging: '打包中', success: '已完成', failed: '失败',
};

export default function StatusBadge({ status }: Props) {
  const [bg, text] = conf[status] || ['bg-gray-100', 'text-gray-600'];
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
      {labels[status] || status}
    </span>
  );
}
