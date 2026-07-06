const API_BASE = '/api/v1';

interface ApiOpts { method?: string; body?: unknown; headers?: Record<string, string> }

async function request<T>(path: string, opts: ApiOpts = {}): Promise<T> {
  const token = localStorage.getItem('nebula_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...opts.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method || 'GET',
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
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
      request<{ status: string; message?: string }>(`/projects/${pid}/build`, { method: 'POST' }),
    status: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/build/status`),
    artifacts: (pid: string) =>
      request<Array<{ version: string; created_at: string; path: string }>>(`/projects/${pid}/build/artifacts`),
  },
};
