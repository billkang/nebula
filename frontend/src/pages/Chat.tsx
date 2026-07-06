import { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import MessageBubble from '../components/MessageBubble';
import MessageInput from '../components/MessageInput';
import ConfirmCard from '../components/ConfirmCard';
import StatusBadge from '../components/StatusBadge';

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const msgEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [reqSummary, setReqSummary] = useState('');
  const [execStatus, setExecStatus] = useState('idle');
  const [buildStatus, setBuildStatus] = useState('idle');

  useEffect(() => {
    if (id) api.sessions.create(id).then((s) => setSessionId(s.id));
  }, [id]);

  const { data: messages } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => {
      if (!id || !sessionId) return Promise.resolve([]);
      return api.sessions.messages(id, sessionId);
    },
    enabled: !!sessionId,
    refetchInterval: 2000,
  });

  const sendMut = useMutation({
    mutationFn: (c: string) => {
      if (!id || !sessionId) return Promise.reject(new Error('未就绪'));
      return api.sessions.send(id, sessionId, c);
    },
    onSuccess: (msgs) => {
      qc.invalidateQueries({ queryKey: ['messages', sessionId] });
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
  };

  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/projects" className="text-gray-400 hover:text-gray-600">← 返回</Link>
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
          </div>
        )}
        <div ref={msgEndRef} />
      </div>
      <MessageInput onSend={(c) => sendMut.mutate(c)} disabled={showConfirm || execStatus !== 'idle'} />
    </div>
  );
}
