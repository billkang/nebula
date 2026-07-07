import ReactMarkdown from 'react-markdown';

interface Props { content: string }

export default function DocViewer({ content }: Props) {
  return (
    <div
      className="prose prose-sm max-w-none"
      style={{
        color: 'var(--color-text-base)',
        '--tw-prose-body': 'var(--color-text-base)',
        '--tw-prose-headings': 'var(--color-text-base)',
        '--tw-prose-links': 'var(--color-primary)',
        '--tw-prose-bold': 'var(--color-text-base)',
        '--tw-prose-code': 'var(--color-text-base)',
        '--tw-prose-quotes': 'var(--color-text-secondary)',
      } as React.CSSProperties}
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
