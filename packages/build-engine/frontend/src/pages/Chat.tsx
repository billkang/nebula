import { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import MessageBubble from '../components/MessageBubble';
import MessageInput from '../components/MessageInput';
import ConfirmCard from '../components/ConfirmCard';
import StatusBadge from '../components/StatusBadge';

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const msgEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [reqSummary, setReqSummary] = useState('');
  const [execStatus, setExecStatus] = useState('idle');
  const [buildStatus, setBuildStatus] = useState('idle');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{ id: string; role: string; content: string; phase?: string; created_at: string }>>([]);
  const [sseConnected, setSseConnected] = useState(false);
  const currentToken = localStorage.getItem('nebula_token');

  useEffect(() => {
    if (id) api.sessions.create(id).then((s) => setSessionId(s.id));
  }, [id]);

  useEffect(() => {
    if (!id || !sessionId || !currentToken) return;

    const es = new EventSource(`/api/v1/projects/${id}/sessions/${sessionId}/messages/stream?token=${currentToken}`);

    es.onopen = () => setSseConnected(true);

    es.onmessage = (e) => {
      try {
        const msgs = JSON.parse(e.data);
        setMessages(msgs);
      } catch { /* ignore parse errors on heartbeat/comment lines */ }
    };

    es.addEventListener('error', () => {
      if (es.readyState === EventSource.CLOSED) {
        setSseConnected(false);
      }
    });

    return () => {
      es.close();
      setSseConnected(false);
    };
  }, [id, sessionId, currentToken]);

  const sendMut = useMutation({
    mutationFn: (c: string) => {
      if (!id || !sessionId) return Promise.reject(new Error('未就绪'));
      return api.sessions.send(id, sessionId, c);
    },
    onMutate: async (c) => {
      // 乐观更新：立即显示用户消息，不等 API 返回
      const optimisticMsg = {
        id: `optimistic-${Date.now()}-${c.length}`,
        role: 'user' as const,
        content: c,
        created_at: new Date().toISOString(),
        phase: undefined,
      };
      setMessages((prev) => [...prev, optimisticMsg]);
    },
    onError: (_err, _c, _ctx) => {
      // 请求失败时移除乐观消息，还原到上一次服务端确认的状态
      setMessages((prev) => prev.filter((m) => !m.id.startsWith('optimistic-')));
    },
    onSuccess: (msgs) => {
      setMessages(msgs); // 直接从 POST 响应更新消息，避免 SSE 延迟/丢失导致 UI 空白
      const last = msgs[msgs.length - 1];
      if (last?.phase === 'confirming') { setShowConfirm(true); setReqSummary(last.content); }
      if (last?.phase === 'generating') setShowConfirm(false);
    },
  });

  const handleConfirm = async () => {
    setShowConfirm(false);
    if (id) await api.docs.generate(id);
    sendMut.mutate('确认，没有问题');
  };

  const handleRevise = () => { setShowConfirm(false); sendMut.mutate('需要调整'); };

  const handleExecute = async () => {
    if (!id) return;
    setExecStatus('running');
    const r = await api.executor.execute(id);
    setExecStatus(r.status);
  };

  const handleBuild = async () => {
    if (!id) return;
    setBuildStatus('running');
    const r = await api.build.trigger(id);
    setBuildStatus(r.status);
    if (r.preview_url) setPreviewUrl(r.preview_url);
    if (r.runtime_status) setRuntimeStatus(r.runtime_status);
  };

  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  return (
    <div className="flex h-full flex-col" style={{ background: 'var(--color-bg-layout)' }}>
      {/* Top bar */}
      <div
        className="flex items-center justify-between border-b px-6 py-3"
        style={{
          background: 'var(--color-bg-container)',
          borderColor: 'var(--color-border)',
        }}
      >
        <div className="flex items-center gap-3">
          <Link
            to="/projects"
            style={{ color: 'var(--color-text-secondary)' }}
            className="text-sm transition-colors duration-150 hover:opacity-80"
          >
            ← 返回
          </Link>
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              sseConnected ? 'animate-pulse' : ''
            }`}
            style={{
              background: sseConnected ? 'var(--color-success)' : 'var(--color-error)',
            }}
            title={sseConnected ? '已连接' : '连接断开'}
          />
          <h2 className="text-base font-semibold" style={{ color: 'var(--color-text-base)' }}>
            需求对话
          </h2>
        </div>
        {messages?.some((m) => m.phase === 'generating') && (
          <div className="flex gap-2">
            <Link
              to={`/projects/${id}/docs`}
              className="rounded-lg px-3 py-1.5 text-sm transition-all duration-150"
              style={{
                background: 'var(--color-primary-bg)',
                color: 'var(--color-primary)',
              }}
            >
              查看文档
            </Link>
            <button
              onClick={handleExecute}
              className="rounded-lg px-3 py-1.5 text-sm text-white transition-all duration-150 hover:scale-[1.02]"
              style={{ background: 'var(--color-primary)' }}
            >
              ⚡ 开始编码
            </button>
          </div>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-auto p-6">
        {messages?.map((m) => (
          <MessageBubble
            key={m.id}
            role={m.role as 'user' | 'agent'}
            content={m.content}
            phase={m.phase}
          />
        ))}

        {/* Typing indicator */}
        {sendMut.isPending && (
          <div className="mb-4 flex justify-start">
            <div
              className="max-w-[70%] rounded-xl p-4"
              style={{
                background: 'var(--color-bg-container)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div className="flex items-center gap-2">
                <span
                  className="inline-block h-2 w-2 animate-bounce rounded-full"
                  style={{ background: 'var(--color-text-secondary)', animationDelay: '0ms' }}
                />
                <span
                  className="inline-block h-2 w-2 animate-bounce rounded-full"
                  style={{ background: 'var(--color-text-secondary)', animationDelay: '150ms' }}
                />
                <span
                  className="inline-block h-2 w-2 animate-bounce rounded-full"
                  style={{ background: 'var(--color-text-secondary)', animationDelay: '300ms' }}
                />
                <span className="ml-1 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  Agent 正在思考…
                </span>
              </div>
            </div>
          </div>
        )}

        {showConfirm && (
          <ConfirmCard summary={reqSummary} onConfirm={handleConfirm} onRevise={handleRevise} />
        )}

        {/* Exec status */}
        {execStatus !== 'idle' && (
          <div
            className="mb-4 rounded-xl p-4"
            style={{
              background: 'var(--color-bg-container)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div className="flex items-center gap-2">
              <span className="text-sm">🔧 编码执行</span>
              <StatusBadge status={execStatus} />
            </div>
            {execStatus === 'success' && (
              <div className="mt-2">
                <button
                  onClick={handleBuild}
                  className="rounded-lg px-3 py-1.5 text-sm text-white"
                  style={{ background: 'var(--color-primary)' }}
                >
                  📦 开始构建
                </button>
              </div>
            )}
          </div>
        )}

        {/* Build status */}
        {buildStatus !== 'idle' && (
          <div
            className="mb-4 rounded-xl p-4"
            style={{
              background: 'var(--color-bg-container)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div className="flex items-center gap-2">
              <span className="text-sm">📦 构建验证</span>
              <StatusBadge status={buildStatus} />
            </div>
            {buildStatus === 'success' && (
              <p className="mt-2 text-sm" style={{ color: 'var(--color-success)' }}>
                ✅ 构建完成
              </p>
            )}
            {previewUrl && (
              <div className="mt-3 flex flex-wrap gap-2">
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg px-3 py-1.5 text-sm text-white transition-all duration-150 hover:scale-[1.02]"
                  style={{ background: 'var(--color-primary)' }}
                >
                  🚀 在 Runtime 中预览
                </a>
                <Link
                  to={`/projects/${id}/sandbox`}
                  className="rounded-lg px-3 py-1.5 text-sm text-white transition-all duration-150 hover:scale-[1.02]"
                  style={{ background: 'var(--color-warning)' }}
                >
                  ✏️ 在沙箱中编辑
                </Link>
                <Link
                  to={`/projects/${id}/docs`}
                  className="rounded-lg px-3 py-1.5 text-sm transition-all duration-150"
                  style={{
                    background: 'var(--color-bg-layout)',
                    color: 'var(--color-text-secondary)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  查看文档
                </Link>
              </div>
            )}
            {runtimeStatus === 'runtime_unavailable' && (
              <p className="mt-1 text-xs" style={{ color: 'var(--color-warning)' }}>
                Runtime 未运行，可稍后手动部署
              </p>
            )}
          </div>
        )}

        <div ref={msgEndRef} />
      </div>

      <MessageInput
        onSend={(c) => sendMut.mutate(c)}
        disabled={showConfirm || execStatus !== 'idle'}
      />
    </div>
  );
}
