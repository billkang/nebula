import ReactMarkdown from 'react-markdown';

interface Props { role: 'user' | 'agent'; content: string; phase?: string }

const phaseLabels: Record<string, string> = {
  greeting: '👋 问候', collecting: '📋 收集需求',
  clarifying: '🤔 澄清细节', confirming: '✅ 确认范围', generating: '📄 生成文档',
};

export default function MessageBubble({ role, content, phase }: Props) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] rounded-lg p-4 ${
        isUser ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200'
      }`}>
        {phase && !isUser && (
          <div className="text-xs text-gray-400 mb-1">{phaseLabels[phase] || phase}</div>
        )}
        {isUser ? <p className="whitespace-pre-wrap">{content}</p> : (
          <div className="prose prose-sm max-w-none"><ReactMarkdown>{content}</ReactMarkdown></div>
        )}
      </div>
    </div>
  );
}
