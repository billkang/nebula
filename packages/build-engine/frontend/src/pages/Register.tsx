import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.auth.register({ username, email, password });
      navigate('/login');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center"
      style={{ background: 'var(--color-bg-layout)' }}
    >
      <div
        className="w-full max-w-sm rounded-2xl p-8 shadow-lg"
        style={{
          background: 'var(--color-bg-container)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="mb-8 text-center">
          <span className="text-3xl" style={{ color: 'var(--color-primary)' }}>
            ✦
          </span>
          <h1
            className="mt-2 text-2xl font-bold"
            style={{ color: 'var(--color-text-base)' }}
          >
            注册账号
          </h1>
          <p
            className="mt-1 text-sm"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            创建你的星云账号
          </p>
        </div>

        {error && (
          <div
            className="mb-4 rounded-lg px-4 py-3 text-sm"
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              color: 'var(--color-error)',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              className="mb-1.5 block text-sm font-medium"
              style={{ color: 'var(--color-text-base)' }}
            >
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
                e.currentTarget.style.boxShadow = '0 0 0 3px var(--color-primary-bg)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              required
              minLength={2}
            />
          </div>
          <div>
            <label
              className="mb-1.5 block text-sm font-medium"
              style={{ color: 'var(--color-text-base)' }}
            >
              邮箱
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
                e.currentTarget.style.boxShadow = '0 0 0 3px var(--color-primary-bg)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              required
            />
          </div>
          <div>
            <label
              className="mb-1.5 block text-sm font-medium"
              style={{ color: 'var(--color-text-base)' }}
            >
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
                e.currentTarget.style.boxShadow = '0 0 0 3px var(--color-primary-bg)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              required
              minLength={6}
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-lg py-2.5 text-sm font-medium text-white transition-all duration-200 hover:scale-[1.02]"
            style={{ background: 'var(--color-primary)' }}
          >
            注册
          </button>
        </form>
        <p
          className="mt-6 text-center text-sm"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          已有账号？{' '}
          <Link
            to="/login"
            style={{ color: 'var(--color-primary)' }}
            className="hover:underline"
          >
            登录
          </Link>
        </p>
      </div>
    </div>
  );
}
