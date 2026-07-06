import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useStore } from '../store';

export default function Sidebar() {
  const navigate = useNavigate();
  const params = useParams();
  const { user, logout, setCurrentProject } = useStore();

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
  });

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-bold">星云 · Nebula</h2>
        <p className="text-sm text-gray-400">{user?.username} ({user?.role})</p>
      </div>
      <div className="flex-1 overflow-auto p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-medium text-gray-300">项目</h3>
          <Link to="/projects" className="text-xs text-blue-400 hover:underline">管理</Link>
        </div>
        {projects?.map((p) => (
          <Link key={p.id} to={`/projects/${p.id}`}
            className={`block px-3 py-2 rounded-md text-sm mb-1 ${
              params.id === p.id ? 'bg-blue-600' : 'hover:bg-gray-700'
            }`}
            onClick={() => setCurrentProject(p.id)}>
            {p.name}
          </Link>
        ))}
      </div>
      <div className="p-4 border-t border-gray-700">
        <button onClick={() => { logout(); navigate('/login'); }}
          className="text-sm text-gray-400 hover:text-white">退出登录</button>
      </div>
    </aside>
  );
}
