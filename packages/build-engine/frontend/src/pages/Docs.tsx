import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import DocViewer from '../components/DocViewer';

export default function Docs() {
  const { id } = useParams<{ id: string }>();
  const [selected, setSelected] = useState('proposal');

  const { data: docs } = useQuery({
    queryKey: ['docs', id],
    queryFn: () => {
      if (!id) return Promise.resolve([]);
      return api.docs.list(id);
    },
    enabled: !!id,
  });

  const { data: content } = useQuery({
    queryKey: ['doc', id, selected],
    queryFn: () => {
      if (!id) return Promise.reject(new Error('未就绪'));
      return api.docs.get(id, selected);
    },
    enabled: !!id && !!selected,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="border-b bg-white px-6 py-3">
        <Link to={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 mr-3">← 返回对话</Link>
        <span className="font-semibold">设计文档</span>
      </div>
      <div className="flex flex-1">
        <div className="w-48 border-r bg-gray-50 p-4">
          {docs?.map((d) => (
            <button key={d.type} onClick={() => setSelected(d.type)}
              className={`block w-full text-left px-3 py-2 rounded-md text-sm mb-1 ${
                selected === d.type ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200'
              }`}>
              {d.type === 'proposal' && '📋 Proposal'}
              {d.type === 'specs' && '📐 Specs'}
              {d.type === 'design' && '🏗️ Design'}
              {d.type === 'tasks' && '✅ Tasks'}
              {!d.exists && ' ⏳'}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-auto p-6">
          {content ? <DocViewer content={content.content} /> : <p className="text-gray-400">选择左侧文档查看</p>}
        </div>
      </div>
    </div>
  );
}
