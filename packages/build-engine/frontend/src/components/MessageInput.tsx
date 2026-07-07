import { useState } from 'react';

interface Props { onSend: (content: string) => void; disabled?: boolean }

export default function MessageInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState('');
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
  };
  return (
    <form
      onSubmit={handleSubmit}
      className="border-t p-4"
      style={{
        borderColor: 'var(--color-border)',
        background: 'var(--color-bg-container)',
      }}
    >
      <div
        className="flex items-center gap-2 rounded-xl border p-2"
        style={{
          background: 'var(--glass-bg)',
          borderColor: 'var(--glass-border)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入你的需求…"
          disabled={disabled}
          className="flex-1 bg-transparent px-3 py-2 text-sm outline-none"
          style={{ color: 'var(--color-text-base)' }}
        />
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="rounded-lg px-4 py-2 text-sm text-white transition-all duration-200 hover:scale-105 disabled:opacity-40"
          style={{ background: 'var(--color-primary)' }}
        >
          发送
        </button>
      </div>
    </form>
  );
}
