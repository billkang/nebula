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

  if (isLoading) return <div className="p-8">加载中...</div>;

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">项目列表</h1>
        <button onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          创建项目
        </button>
      </div>
      {showCreate && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-lg font-semibold mb-4">新建项目</h2>
          <div className="space-y-3">
            <input type="text" placeholder="项目名称" value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border rounded-md" />
            <textarea placeholder="项目描述（可选）" value={desc}
              onChange={(e) => setDesc(e.target.value)} className="w-full px-3 py-2 border rounded-md" rows={3} />
            <div className="flex gap-2">
              <button onClick={() => createMut.mutate({ name, description: desc })}
                disabled={!name}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
                创建
              </button>
              <button onClick={() => setShowCreate(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-50">取消</button>
            </div>
          </div>
        </div>
      )}
      {projects?.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg mb-2">还没有项目</p>
          <p>点击「创建项目」开始你的第一个星云项目</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects?.map((p) => (
            <div key={p.id} onClick={() => navigate(`/projects/${p.id}`)}
              className="bg-white p-6 rounded-lg shadow-md cursor-pointer hover:shadow-lg transition-shadow">
              <h3 className="font-semibold text-lg mb-2">{p.name}</h3>
              {p.description && <p className="text-gray-500 text-sm mb-3">{p.description}</p>}
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">{new Date(p.created_at).toLocaleDateString('zh-CN')}</span>
                <button onClick={(e) => { e.stopPropagation(); deleteMut.mutate(p.id); }}
                  className="text-xs text-red-500 hover:underline">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
