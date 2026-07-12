const API_BASE = '/api/v1';
import { logger } from '../utils/logger';

interface ApiOpts { method?: string; body?: unknown; headers?: Record<string, string> }

async function request<T>(path: string, opts: ApiOpts = {}): Promise<T> {
  const token = localStorage.getItem('nebula_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...opts.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const method = opts.method || 'GET';
  const fullPath = `${API_BASE}${path}`;

  logger.info(`API ${method} ${path}`);

  try {
    const res = await fetch(fullPath, {
      method,
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });

    if (res.status === 401) {
      logger.warn('Auth token expired, redirecting to login');
      localStorage.removeItem('nebula_token');
      window.location.href = '/login';
      throw new Error('登录已过期，请重新登录');
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '请求失败' }));
      logger.error(`API ${method} ${path} → ${res.status}`, err.detail);
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    logger.info(`API ${method} ${path} → ${res.status}`);
    return res.json();
  } catch (err) {
    if (err instanceof TypeError) {
      // Network error
      logger.error(`API ${method} ${path} — network error`, err);
    }
    throw err;
  }
}

export const api = {
  auth: {
    register: (d: { username: string; email: string; password: string }) =>
      request<{ id: string; username: string }>('/auth/register', { method: 'POST', body: d }),
    login: (d: { username: string; password: string }) =>
      request<{ access_token: string; user: { id: string; username: string; email: string; role: string } }>(
        '/auth/login', { method: 'POST', body: d }),
    me: () => request<{ id: string; username: string; role: string; email: string }>('/auth/me'),
  },
  projects: {
    list: () => request<Array<{ id: string; name: string; description: string; created_at: string }>>('/projects'),
    create: (d: { name: string; description?: string }) =>
      request<{ id: string; name: string; description: string }>('/projects', { method: 'POST', body: d }),
    get: (id: string) => request<{ id: string; name: string; description: string }>(`/projects/${id}`),
    delete: (id: string) => request<{ message: string }>(`/projects/${id}`, { method: 'DELETE' }),
  },
  sessions: {
    list: (pid: string) =>
      request<Array<{ id: string; status: string }>>(`/projects/${pid}/sessions`),
    create: (pid: string) =>
      request<{ id: string; project_id: string; status: string }>(
        `/projects/${pid}/sessions`, { method: 'POST' }),
    messages: (pid: string, sid: string) =>
      request<Array<{ id: string; role: string; content: string; phase?: string; created_at: string }>>(
        `/projects/${pid}/sessions/${sid}/messages`),
    send: (pid: string, sid: string, content: string) =>
      request<Array<{ id: string; role: string; content: string; phase?: string; created_at: string }>>(
        `/projects/${pid}/sessions/${sid}/messages`, { method: 'POST', body: { content } }),
  },
  docs: {
    list: (pid: string) => request<Array<{ type: string; exists: boolean }>>(`/projects/${pid}/docs`),
    get: (pid: string, type: string) =>
      request<{ type: string; content: string }>(`/projects/${pid}/docs/${type}`),
    generate: (pid: string) =>
      request<{ success: boolean; message: string }>(`/projects/${pid}/docs/generate`, { method: 'POST' }),
  },
  executor: {
    execute: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/execute`, { method: 'POST' }),
    status: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/execute/status`),
  },
  build: {
    trigger: (pid: string) =>
      request<{ status: string; message?: string; artifact_version?: string; runtime_status?: string; preview_url?: string }>(`/projects/${pid}/build`, { method: 'POST' }),
    status: (pid: string) =>
      request<{ status: string; message?: string; artifact_version?: string; runtime_status?: string; preview_url?: string }>(`/projects/${pid}/build/status`),
    artifacts: (pid: string) =>
      request<Array<{ version: string; created_at: string; path: string }>>(`/projects/${pid}/build/artifacts`),
    deploy: (pid: string, version: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/build/deploy?version=${version}`, { method: 'POST' }),
    runtimeStatus: (pid: string) =>
      request<{ status: string; url?: string }>(`/projects/${pid}/build/runtime-status`),
  },
  sandbox: {
    init: (pid: string, version?: string) =>
      request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/init${version ? `?artifact_version=${version}` : ''}`, { method: 'POST' }),
    files: (pid: string) =>
      request<{ data: { files: any[]; meta: any }; error: string | null }>(`/projects/${pid}/sandbox/files`),
    getFile: (pid: string, path: string) =>
      request<{ data: { path: string; content: string }; error: string | null }>(`/projects/${pid}/sandbox/files/${encodePath(path)}`),
    saveFile: (pid: string, path: string, content: string) =>
      request<{ data: { path: string; saved: boolean; modified: boolean }; error: string | null }>(`/projects/${pid}/sandbox/files/${encodePath(path)}`, { method: 'PUT', body: { content } }),
    snapshots: {
      list: (pid: string) =>
        request<{ data: any[]; error: string | null }>(`/projects/${pid}/sandbox/snapshots`),
      create: (pid: string, description?: string) =>
        request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/snapshots`, { method: 'POST', body: { description } }),
      restore: (pid: string, sid: string) =>
        request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/restore/${sid}`, { method: 'POST' }),
    },
    diff: (pid: string, path: string) =>
      request<{ data: { path: string; has_diff: boolean; diff: string; summary: string; additions?: number; removals?: number }; error: string | null }>(`/projects/${pid}/sandbox/diff/${encodePath(path)}`),
    rebuild: (pid: string, description?: string, async?: boolean) =>
      request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/rebuild`, { method: 'POST', body: { description, async } }),
    restoreOriginal: (pid: string, filePath?: string) =>
      request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/restore-original`, { method: 'POST', body: filePath ? { file_path: filePath } : {} }),
    rebuildStatus: (pid: string) =>
      request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/rebuild/status`),
    cancelRebuild: (pid: string) =>
      request<{ data: any; error: string | null }>(`/projects/${pid}/sandbox/rebuild/cancel`, { method: 'POST' }),
  },
};

function encodePath(p: string): string {
  return p.split('/').map(encodeURIComponent).join('/');
}
