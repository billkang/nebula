import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export default function Projects() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
  });

  const createMut = useMutation({
    mutationFn: (d: { name: string; description?: string }) => api.projects.create(d),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ['projects'] });
      setShowCreate(false); setName(''); setDesc('');
      navigate(`/projects/${p.id}`);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.projects.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  });

  if (isLoading)
    return (
      <div className="p-8">
        <div className="mb-6 flex items-center justify-between">
          <div className="h-8 w-32 animate-pulse rounded-lg" style={{ background: 'var(--color-border)' }} />
          <div className="h-10 w-24 animate-pulse rounded-lg" style={{ background: 'var(--color-border)' }} />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-xl p-6"
              style={{
                background: 'var(--color-bg-container)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div className="mb-3 h-5 w-3/4 rounded" style={{ background: 'var(--color-border)' }} />
              <div className="h-4 w-1/2 rounded" style={{ background: 'var(--color-border)' }} />
            </div>
          ))}
        </div>
      </div>
    );

  return (
    <div className="p-0">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-base)' }}>
          项目列表
        </h1>
        <button
          onClick={() => setShowCreate(true)}
          className="rounded-lg px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:scale-[1.02]"
          style={{ background: 'var(--color-primary)' }}
        >
          创建项目
        </button>
      </div>

      {showCreate && (
        <div
          className="mb-6 rounded-xl p-6 shadow-sm"
          style={{
            background: 'var(--color-bg-container)',
            border: '1px solid var(--color-border)',
          }}
        >
          <h2 className="mb-4 text-lg font-semibold" style={{ color: 'var(--color-text-base)' }}>
            新建项目
          </h2>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="项目名称"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
              }}
            />
            <textarea
              placeholder="项目描述（可选）"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={3}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
              }}
            />
            <div className="flex gap-2">
              <button
                onClick={() => createMut.mutate({ name, description: desc })}
                disabled={!name}
                className="rounded-lg px-4 py-2 text-sm text-white transition-all duration-200 hover:scale-[1.02] disabled:opacity-40"
                style={{ background: 'var(--color-primary)' }}
              >
                创建
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="rounded-lg border px-4 py-2 text-sm transition-all duration-150"
                style={{
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text-base)',
                }}
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {projects?.length === 0 ? (
        <div className="py-16 text-center" style={{ color: 'var(--color-text-secondary)' }}>
          <p className="mb-2 text-lg">还没有项目</p>
          <p className="text-sm">点击「创建项目」开始你的第一个星云项目</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects?.map((p) => (
            <div
              key={p.id}
              onClick={() => navigate(`/projects/${p.id}`)}
              className="cursor-pointer rounded-xl p-6 transition-all duration-200 hover:scale-[1.02]"
              style={{
                background: 'var(--color-bg-container)',
                border: '1px solid var(--color-border)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <h3 className="mb-2 text-base font-semibold" style={{ color: 'var(--color-text-base)' }}>
                {p.name}
              </h3>
              {p.description && (
                <p className="mb-3 text-sm line-clamp-2" style={{ color: 'var(--color-text-secondary)' }}>
                  {p.description}
                </p>
              )}
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                  {new Date(p.created_at).toLocaleDateString('zh-CN')}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteMut.mutate(p.id);
                  }}
                  className="text-xs transition-colors duration-150"
                  style={{ color: 'var(--color-error)' }}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
