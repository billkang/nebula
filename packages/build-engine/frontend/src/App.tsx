import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useStore } from './store';
import Login from './pages/Login';
import Register from './pages/Register';
import Projects from './pages/Projects';
import Chat from './pages/Chat';
import Docs from './pages/Docs';
import SandboxPage from './pages/Sandbox';
import AppLayout from './components/AppLayout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return useStore((s) => s.token) ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  const location = useLocation();

  return (
    <div key={location.pathname} className="page-enter">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/projects" element={<ProtectedRoute><AppLayout><Projects /></AppLayout></ProtectedRoute>} />
        <Route path="/projects/:id" element={<ProtectedRoute><AppLayout><Chat /></AppLayout></ProtectedRoute>} />
        <Route path="/projects/:id/docs" element={<ProtectedRoute><AppLayout><Docs /></AppLayout></ProtectedRoute>} />
        <Route path="/projects/:id/sandbox" element={<ProtectedRoute><AppLayout><SandboxPage /></AppLayout></ProtectedRoute>} />
        <Route path="/" element={<Navigate to="/projects" replace />} />
      </Routes>
    </div>
  );
}
