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
    onSuccess: (msgs) => {
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
    <div className="flex flex-col h-full">
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/projects" className="text-gray-400 hover:text-gray-600">← 返回</Link>
          <span className={`inline-block w-2 h-2 rounded-full ${sseConnected ? 'bg-green-500' : 'bg-red-400'}`}
                title={sseConnected ? '已连接' : '连接断开'} />
          <h2 className="font-semibold">需求对话</h2>
        </div>
        {messages?.some((m) => m.phase === 'generating') && (
          <div className="flex gap-2">
            <Link to={`/projects/${id}/docs`}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200">
              查看文档
            </Link>
            <button onClick={handleExecute}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700">
              ⚡ 开始编码
            </button>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        {messages?.map((m) => (
          <MessageBubble key={m.id} role={m.role as 'user' | 'agent'} content={m.content} phase={m.phase} />
        ))}
        {sendMut.isPending && (
          <div className="flex justify-start mb-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4 max-w-[70%]">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="text-sm text-gray-500 ml-1">Agent 正在思考…</span>
              </div>
            </div>
          </div>
        )}
        {showConfirm && <ConfirmCard summary={reqSummary} onConfirm={handleConfirm} onRevise={handleRevise} />}
        {execStatus !== 'idle' && (
          <div className="bg-white border rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm">🔧 编码执行</span>
              <StatusBadge status={execStatus} />
            </div>
            {execStatus === 'success' && (
              <div className="mt-2">
                <button onClick={handleBuild}
                  className="px-3 py-1 text-sm bg-purple-600 text-white rounded-md">
                  📦 开始构建
                </button>
              </div>
            )}
          </div>
        )}
        {buildStatus !== 'idle' && (
          <div className="bg-white border rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm">📦 构建验证</span>
              <StatusBadge status={buildStatus} />
            </div>
            {buildStatus === 'success' && <p className="text-sm text-green-600 mt-2">✅ 构建完成</p>}
            {previewUrl && (
              <div className="mt-3 flex gap-2">
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  🚀 在 Runtime 中预览
                </a>
                <Link
                  to={`/projects/${id}/sandbox`}
                  className="px-3 py-1 text-sm bg-amber-500 text-white rounded-md hover:bg-amber-600"
                >
                  ✏️ 在沙箱中编辑
                </Link>
                <Link
                  to={`/projects/${id}/docs`}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  查看文档
                </Link>
              </div>
            )}
            {runtimeStatus === 'runtime_unavailable' && (
              <p className="text-xs text-amber-600 mt-1">Runtime 未运行，可稍后手动部署</p>
            )}
          </div>
        )}
        <div ref={msgEndRef} />
      </div>
      <MessageInput onSend={(c) => sendMut.mutate(c)} disabled={showConfirm || execStatus !== 'idle'} />
    </div>
  );
}
