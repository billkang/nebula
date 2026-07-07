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
    <div className="flex h-full flex-col">
      <div
        className="flex items-center border-b px-6 py-3"
        style={{
          borderColor: 'var(--color-border)',
          background: 'var(--color-bg-container)',
        }}
      >
        <Link
          to={`/projects/${id}`}
          className="mr-3 text-sm transition-colors duration-150"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          ← 返回对话
        </Link>
        <span className="text-base font-semibold" style={{ color: 'var(--color-text-base)' }}>
          设计文档
        </span>
      </div>
      <div className="flex flex-1">
        <div
          className="w-48 border-r p-4"
          style={{
            borderColor: 'var(--color-border)',
            background: 'var(--color-bg-layout)',
          }}
        >
          {docs?.map((d) => (
            <button
              key={d.type}
              onClick={() => setSelected(d.type)}
              className="mb-1 block w-full rounded-lg px-3 py-2 text-left text-sm transition-all duration-150"
              style={{
                background:
                  selected === d.type
                    ? 'var(--sidebar-active-bg)'
                    : 'transparent',
                color:
                  selected === d.type
                    ? 'var(--color-primary)'
                    : 'var(--sidebar-text)',
              }}
              onMouseEnter={(e) => {
                if (selected !== d.type)
                  e.currentTarget.style.background = 'var(--sidebar-active-bg)';
              }}
              onMouseLeave={(e) => {
                if (selected !== d.type)
                  e.currentTarget.style.background = 'transparent';
              }}
            >
              {d.type === 'proposal' && '📋 Proposal'}
              {d.type === 'specs' && '📐 Specs'}
              {d.type === 'design' && '🏗️ Design'}
              {d.type === 'tasks' && '✅ Tasks'}
              {!d.exists && ' ⏳'}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-auto p-6" style={{ color: 'var(--color-text-secondary)' }}>
          {content ? (
            <DocViewer content={content.content} />
          ) : (
            <p className="text-sm">选择左侧文档查看</p>
          )}
        </div>
      </div>
    </div>
  );
}
