import ReactMarkdown from 'react-markdown';

interface Props { content: string }

export default function DocViewer({ content }: Props) {
  return <div className="prose prose-sm max-w-none"><ReactMarkdown>{content}</ReactMarkdown></div>;
}
