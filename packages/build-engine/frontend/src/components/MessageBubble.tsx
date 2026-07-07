import ReactMarkdown from 'react-markdown';

interface Props { role: 'user' | 'agent'; content: string; phase?: string }

const phaseLabels: Record<string, string> = {
  greeting: '👋 问候', collecting: '📋 收集需求',
  clarifying: '🤔 澄清细节', confirming: '✅ 确认范围', generating: '📄 生成文档',
};

export default function MessageBubble({ role, content, phase }: Props) {
  const isUser = role === 'user';
  return (
    <div className={`mb-4 flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className="animate-[slideUp_0.3s_ease-out] max-w-[75%] rounded-2xl px-4 py-3"
        style={{
          background: isUser ? 'var(--color-primary)' : 'var(--color-bg-container)',
          color: isUser ? '#FFFFFF' : 'var(--color-text-base)',
          border: isUser ? 'none' : '1px solid var(--color-border)',
          borderBottomRightRadius: isUser ? 4 : 16,
          borderBottomLeftRadius: isUser ? 16 : 4,
        }}
      >
        {phase && !isUser && (
          <div className="mb-1 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            {phaseLabels[phase] || phase}
          </div>
        )}
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
        ) : (
          <div className="prose prose-sm max-w-none" style={{ color: 'var(--color-text-base)' }}>
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
