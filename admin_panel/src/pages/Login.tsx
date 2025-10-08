import { useMemo, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function Login() {
  const { signInWithGoogle, signInWithEmail, signUpWithEmail, resetPassword } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remember, setRemember] = useState(false);

  const title = useMemo(() => (mode === 'signin' ? 'Welcome back' : 'Create your admin account'), [mode]);
  const cta = useMemo(() => (mode === 'signin' ? 'Sign in' : 'Create account'), [mode]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === 'signin') {
        await signInWithEmail(email, password, remember);
      } else {
        await signUpWithEmail(email, password);
      }
      navigate('/');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Authentication failed';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      display: 'grid',
      placeItems: 'center',
      minHeight: '100vh',
      background: '#eef2f7',
      padding: 16,
    }}>
      <div style={{ width: '100%', maxWidth: 460, background: 'white', borderRadius: 16, boxShadow: '0 10px 30px rgba(0,0,0,0.08)', overflow: 'hidden', border: '1px solid #e5e7eb' }}>
        <div style={{ padding: 28, borderBottom: '1px solid #f1f5f9', background: '#fff' }}>
          <h2 style={{ margin: 0, fontSize: 22, color: '#0f172a' }}>{title}</h2>
          <p style={{ margin: '6px 0 0 0', color: '#6b7280', fontSize: 14 }}>Sign into your account</p>
        </div>

        <form onSubmit={onSubmit} style={{ padding: 24, display: 'grid', gap: 12 }}>
          {error && (
            <div style={{ background: '#fef2f2', color: '#991b1b', padding: '10px 12px', borderRadius: 8, fontSize: 14 }}>
              {error}
            </div>
          )}

          <div style={{ display: 'grid', gap: 6 }}>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={{
                padding: '12px 14px',
                border: '1px solid #e2e8f0',
                borderRadius: 10,
                fontSize: 14,
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'grid', gap: 6 }}>
           <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              style={{
                padding: '12px 14px',
                border: '1px solid #e2e8f0',
                borderRadius: 10,
                fontSize: 14,
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: '#0f172a', fontSize: 14 }}>
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              Remember me
            </label>
            <button type="button" onClick={async () => { if (!email) { setError('Enter your email to reset password'); return; } try { setSubmitting(true); setError(null); await resetPassword(email); alert('Password reset email sent.'); } catch (e) { setError(e instanceof Error ? e.message : 'Failed to send reset email'); } finally { setSubmitting(false); } }} style={{ background: 'transparent', border: 0, color: '#111827', cursor: 'pointer', textDecoration: 'underline', fontSize: 14 }}>Forgot password?</button>
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              padding: '12px 16px',
              background: '#0b0b0b',
              color: 'white',
              border: 0,
              borderRadius: 10,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {submitting ? 'Please wait…' : cta}
          </button>

          <div style={{ display: 'grid', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ height: 1, background: '#e5e7eb', flex: 1 }} />
              <span style={{ color: '#6b7280', fontSize: 12 }}>or</span>
              <div style={{ height: 1, background: '#e5e7eb', flex: 1 }} />
            </div>
            <button
              type="button"
              onClick={() => signInWithGoogle()}
              disabled={submitting}
              style={{
                padding: '12px 16px',
                background: 'white',
                color: '#111827',
                border: '1px solid #e5e7eb',
                borderRadius: 10,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12  s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C33.441,6.053,28.973,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20  s20-8.955,20-20C44,22.641,43.862,21.35,43.611,20.083z"/><path fill="#FF3D00" d="M6.305,14.691l6.571,4.819C14.655,16.104,18.961,14,24,14c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657  C33.441,6.053,28.973,4,24,4C16.318,4,8.387,8.065,6.305,14.691z"/><path fill="#4CAF50" d="M24,44c4.874,0,9.304-1.824,12.57-4.829l-5.799-4.914C29.695,36.521,27.005,37,24,37c-5.202,0-9.619-3.317-11.283-7.946  l-6.561,5.046C8.37,40.556,15.624,44,24,44z"/><path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12  s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C33.441,6.053,28.973,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20  s20-8.955,20-20C44,22.641,43.862,21.35,43.611,20.083z"/></svg>
              Continue with Google
            </button>
          </div>

          
        </form>
      </div>
    </div>
  );
}
