import { create } from 'zustand';

interface User { id: string; username: string; email: string; role: string }

interface AppState {
  user: User | null;
  token: string | null;
  currentProjectId: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  setCurrentProject: (id: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  user: null,
  token: localStorage.getItem('nebula_token'),
  currentProjectId: null,
  setAuth: (user, token) => {
    localStorage.setItem('nebula_token', token);
    set({ user, token });
  },
  logout: () => {
    localStorage.removeItem('nebula_token');
    set({ user: null, token: null, currentProjectId: null });
  },
  setCurrentProject: (id) => set({ currentProjectId: id }),
}));
