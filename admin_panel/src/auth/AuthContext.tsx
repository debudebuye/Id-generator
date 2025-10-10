import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { auth, googleProvider } from '../firebase';
import {
  type User,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  setPersistence,
  browserLocalPersistence,
  browserSessionPersistence,
  sendPasswordResetEmail,
} from 'firebase/auth';
import { Navigate } from 'react-router-dom';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string, remember?: boolean) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  signOutUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const DEFAULT_PASSWORD = (import.meta.env.VITE_DEFAULT_ADMIN_PASSWORD as string | undefined) ?? 'admin12345';
  // Fixed credentials for development convenience. Override with VITE_FIXED_EMAIL / VITE_FIXED_PASSWORD if desired.
  const FIXED_EMAIL = (import.meta.env.VITE_FIXED_EMAIL as string | undefined) ?? 'debiansilase@gmail.com';
  const FIXED_PASSWORD = (import.meta.env.VITE_FIXED_PASSWORD as string | undefined) ?? '1234abcd';
  const LOCAL_AUTH_ENABLED = ((import.meta.env.VITE_LOCAL_AUTH as string | undefined) ?? 'true') === 'true';

  useEffect(() => {
    if (LOCAL_AUTH_ENABLED) {
      // Check for persisted user in localStorage
      const persistedUser = localStorage.getItem('admin_user');
      if (persistedUser) {
        try {
          const userData = JSON.parse(persistedUser);
          setUser(userData);
        } catch (e) {
          localStorage.removeItem('admin_user');
        }
      }
      setLoading(false);
      return;
    }
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
    });
    return () => unsub();
  }, [LOCAL_AUTH_ENABLED]);

  const signInWithGoogle = async () => {
    if (LOCAL_AUTH_ENABLED) return;
    await signInWithPopup(auth, googleProvider);
  };

  const signInWithEmail = async (email: string, password: string, remember: boolean = false) => {
    if (LOCAL_AUTH_ENABLED) {
      if (email === FIXED_EMAIL && password === FIXED_PASSWORD) {
        const fakeUser = { uid: 'local-user', email: FIXED_EMAIL } as unknown as User;
        setUser(fakeUser);
        // Persist user in localStorage to prevent auto-logout on refresh
        localStorage.setItem('admin_user', JSON.stringify(fakeUser));
        return;
      }
      throw new Error('Invalid credentials');
    }
    const effectiveEmail = FIXED_EMAIL ?? email;
    const chosenPassword = FIXED_PASSWORD ?? (password && password.length > 0 ? password : DEFAULT_PASSWORD);
    await setPersistence(auth, remember ? browserLocalPersistence : browserSessionPersistence);
    await signInWithEmailAndPassword(auth, effectiveEmail, chosenPassword);
  };

  const signUpWithEmail = async (email: string, password: string) => {
    await createUserWithEmailAndPassword(auth, email, password);
  };

  const resetPassword = async (email: string) => {
    if (LOCAL_AUTH_ENABLED) return;
    await sendPasswordResetEmail(auth, email);
  };

  const signOutUser = async () => {
    if (LOCAL_AUTH_ENABLED) {
      setUser(null);
      localStorage.removeItem('admin_user');
      return;
    }
    await signOut(auth);
  };

  const value = useMemo(
    () => ({ user, loading, signInWithGoogle, signInWithEmail, signUpWithEmail, resetPassword, signOutUser }),
    [user, loading]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
