import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import { AuthProvider, ProtectedRoute, useAuth } from './auth/AuthContext';
import Login from './pages/Login';
import Approvals from './pages/Approvals';
import Approved from './pages/Approved';
import Rejected from './pages/Rejected';
import Users from './pages/Users';
import Allowlist from './pages/Allowlist';
import NewComer from './pages/NewComer';
import DailyReport from './pages/DailyReport';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import './App.css';

function Layout({ children }: { children: React.ReactNode }) {
  const { user, signOutUser } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc' }}>
      <nav style={{
        width: 240,
        background: '#0f172a',
        color: 'white',
        padding: '24px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>
        <h1 style={{ margin: '0 0 24px 0', fontSize: 20, fontWeight: 700 }}>Admin Panel</h1>
        
        <NavLink 
          to="/approvals"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Approvals
        </NavLink>
        <NavLink 
          to="/approved"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Approved
        </NavLink>
        <NavLink 
          to="/rejected"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Rejected
        </NavLink>
        <NavLink 
          to="/users"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Users
        </NavLink>
        <NavLink 
          to="/allowlist"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Allowlist
        </NavLink>
        <NavLink 
          to="/newcomer"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          New Comer
        </NavLink>
        <NavLink 
          to="/daily-report"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Daily Report
        </NavLink>
        <NavLink 
          to="/logs"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Logs
        </NavLink>
        <NavLink 
          to="/settings"
          style={({ isActive }) => ({
            padding: '10px 16px',
            borderRadius: 8,
            textDecoration: 'none',
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            background: isActive ? '#1e293b' : 'transparent',
            display: 'block',
          })}
        >
          Settings
        </NavLink>

        <div style={{ marginTop: 'auto', paddingTop: 24, borderTop: '1px solid #334155' }}>
          <div style={{ fontSize: 14, marginBottom: 12, color: '#94a3b8' }}>
            {user?.email}
          </div>
          <button
            onClick={signOutUser}
            style={{
              width: '100%',
              padding: '10px 16px',
              background: '#1e293b',
              color: 'white',
              border: 0,
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            Sign Out
          </button>
        </div>
      </nav>

      <main style={{ flex: 1, padding: 32 }}>
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <Navigate to="/approvals" replace />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/approvals"
            element={
              <ProtectedRoute>
                <Layout>
                  <Approvals />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/approved"
            element={
              <ProtectedRoute>
                <Layout>
                  <Approved />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/rejected"
            element={
              <ProtectedRoute>
                <Layout>
                  <Rejected />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <Layout>
                  <Users />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/allowlist"
            element={
              <ProtectedRoute>
                <Layout>
                  <Allowlist />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/newcomer"
            element={
              <ProtectedRoute>
                <Layout>
                  <NewComer />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/daily-report"
            element={
              <ProtectedRoute>
                <Layout>
                  <DailyReport />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/logs"
            element={
              <ProtectedRoute>
                <Layout>
                  <Logs />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Layout>
                  <Settings />
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
