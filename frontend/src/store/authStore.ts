import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface AuthState {
    isAuthenticated: boolean;
    login: (username: string, pass: string) => boolean;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            isAuthenticated: false,
            login: (username, pass) => {
                if (username === 'Admin' && pass === 'operator123-') {
                    set({ isAuthenticated: true });
                    return true;
                }
                return false;
            },
            logout: () => set({ isAuthenticated: false }),
        }),
        {
            name: 'meridyen-auth',
            storage: createJSONStorage(() => sessionStorage),
        }
    )
);
