import { Routes, Route, Navigate } from 'react-router-dom';
import { useStore } from './store';
import Login from './pages/Login';
import Register from './pages/Register';
import Projects from './pages/Projects';
import Chat from './pages/Chat';
import Docs from './pages/Docs';
import AppLayout from './components/AppLayout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return useStore((s) => s.token) ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/projects" element={<ProtectedRoute><AppLayout><Projects /></AppLayout></ProtectedRoute>} />
      <Route path="/projects/:id" element={<ProtectedRoute><AppLayout><Chat /></AppLayout></ProtectedRoute>} />
      <Route path="/projects/:id/docs" element={<ProtectedRoute><AppLayout><Docs /></AppLayout></ProtectedRoute>} />
      <Route path="/" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}
