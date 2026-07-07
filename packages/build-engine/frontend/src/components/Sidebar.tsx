import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useStore } from '../store';
import ThemeToggle from './ThemeToggle';

export default function Sidebar() {
  const navigate = useNavigate();
  const params = useParams();
  const { user, logout, setCurrentProject } = useStore();

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside
      className="flex h-screen w-64 flex-col border-r"
      style={{
        background: 'var(--sidebar-bg)',
        borderColor: 'var(--sidebar-border)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5">
        <span className="text-xl" style={{ color: 'var(--color-primary)' }}>
          ✦
        </span>
        <span className="text-lg font-semibold" style={{ color: 'var(--sidebar-text)' }}>
          星云
        </span>
      </div>

      {/* 项目列表 */}
      <div className="flex-1 overflow-auto px-3">
        <div className="mb-3 flex items-center justify-between px-3">
          <span
            className="text-xs font-medium uppercase tracking-wider"
            style={{ color: 'var(--sidebar-text-secondary)' }}
          >
            项目
          </span>
          <Link
            to="/projects"
            className="text-xs transition-colors duration-150"
            style={{ color: 'var(--color-primary)' }}
          >
            管理
          </Link>
        </div>
        <div className="space-y-0.5">
          {projects?.map((p: any) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              onClick={() => setCurrentProject(p.id)}
              className="block rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150"
              style={{
                background:
                  params.id === p.id ? 'var(--sidebar-active-bg)' : 'transparent',
                color:
                  params.id === p.id
                    ? 'var(--color-primary)'
                    : 'var(--sidebar-text)',
              }}
              onMouseEnter={(e) => {
                if (params.id !== p.id)
                  e.currentTarget.style.background = 'var(--sidebar-active-bg)';
              }}
              onMouseLeave={(e) => {
                if (params.id !== p.id)
                  e.currentTarget.style.background = 'transparent';
              }}
            >
              <div className="truncate">{p.name}</div>
            </Link>
          ))}
        </div>
      </div>

      {/* 底部：用户信息 + 主题切换 + 登出 */}
      <div
        className="border-t px-3 py-3"
        style={{ borderColor: 'var(--sidebar-border)' }}
      >
        <div className="flex items-center justify-between rounded-lg px-3 py-2">
          <div className="flex flex-col">
            <span className="text-sm font-medium" style={{ color: 'var(--sidebar-text)' }}>
              {user?.username || '用户'}
            </span>
            <span className="text-xs" style={{ color: 'var(--sidebar-text-secondary)' }}>
              {user?.role || ''}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              onClick={handleLogout}
              className="rounded-md p-1.5 transition-colors duration-150"
              style={{ color: 'var(--sidebar-text-secondary)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-error)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
              }}
              title="退出登录"
              aria-label="退出登录"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
