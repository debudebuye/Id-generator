import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, ProtectedRoute, useAuth } from './auth/AuthContext'
import Login from './pages/Login'
import Settings from './pages/Settings'
import Approvals from './pages/Approvals'
import Approved from './pages/Approved'
import Allowlist from './pages/Allowlist'
import NewComer from './pages/NewComer'
import DailyReport from './pages/DailyReport'
import Rejected from './pages/Rejected'
import Users from './pages/Users'

function Nav() {
  const { user, signOutUser } = useAuth()
  return (
    <nav style={{ display: 'flex', gap: 12, padding: 12, borderBottom: '1px solid #eee' }}>
      <Link to="/">Settings</Link>
      <Link to="/approvals">Approvals</Link>
      <Link to="/allowlist">Allowlist</Link>
      <Link to="/logs">Logs</Link>
      <div style={{ marginLeft: 'auto' }}>
        {user && (
          <>
            <span style={{ marginRight: 8 }}>{user.email}</span>
            <button onClick={signOutUser}>Sign out</button>
          </>
        )}
      </div>
    </nav>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <NewComer />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/new-comer"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <NewComer />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/rejected"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Rejected />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/approved"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Approved />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Users />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Settings />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/daily-report"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <DailyReport />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      {/* Legacy routes for backward compatibility */}
      <Route
        path="/approvals"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <NewComer />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/allowlist"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Users />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

function AuthGate({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  if (!user) return null
  return <>{children}</>
}

function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, signOutUser } = useAuth()
  const location = useLocation()

  const title = (() => {
    const path = location.pathname
    if (path.startsWith('/new-comer')) return 'New Comer'
    if (path.startsWith('/rejected')) return 'Rejected'
    if (path.startsWith('/approved')) return 'Approved'
    if (path.startsWith('/users')) return 'Users'
    if (path.startsWith('/settings')) return 'Settings'
    if (path.startsWith('/daily-report')) return 'Daily Report'
    if (path.startsWith('/approvals')) return 'New Comer' // Legacy redirect
    if (path.startsWith('/allowlist')) return 'Users' // Legacy redirect
    if (path === '/') return 'New Comer'
    return 'New Comer'
  })()
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', height: '100vh', background: '#0b1220' }}>
      {/* Sidebar */}
      <aside style={{ background: 'linear-gradient(180deg, #0b1220 0%, #0f172a 100%)', color: 'white', padding: 16, borderRight: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ fontWeight: 800, letterSpacing: 0.5, marginBottom: 20 }}>Admin Dashboard</div>
        <nav style={{ display: 'grid', gap: 6 }}>
          <SidebarLink to="/new-comer" label="New Comer" />
          <SidebarLink to="/rejected" label="Rejected" />
          <SidebarLink to="/approved" label="Approved" />
          <SidebarLink to="/users" label="Users" />
          <SidebarLink to="/settings" label="Settings" />
          <SidebarLink to="/daily-report" label="Daily Report" />
        </nav>
      </aside>

      {/* Main */}
      <div style={{ display: 'grid', gridTemplateRows: '64px 1fr', background: 'linear-gradient(180deg, #0b1220 0%, #0e1526 100%)' }}>
        <header style={{ position: 'sticky', top: 0, zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', background: 'rgba(15,23,42,0.75)', backdropFilter: 'blur(8px)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ color: 'white', fontWeight: 700 }}>{title}</div>
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ color: 'white', fontSize: 14, opacity: 0.9 }}>{user.email}</span>
              <button onClick={signOutUser} style={{ background: 'white', color: '#0f172a', border: 0, borderRadius: 8, padding: '8px 12px', fontWeight: 600, cursor: 'pointer' }}>Sign out</button>
            </div>
          )}
        </header>
        <main style={{ padding: 24 }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: 16 }}>
            <div style={{ background: 'white', borderRadius: 14, padding: 20, boxShadow: '0 10px 30px rgba(0,0,0,0.08)', border: '1px solid #e5e7eb', minHeight: 'calc(100vh - 64px - 48px)' }}>
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

function SidebarLink({ to, label }: { to: string, label: string }) {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        padding: '10px 12px',
        borderRadius: 10,
        color: 'white',
        textDecoration: 'none',
        background: isActive ? 'rgba(255,255,255,0.12)' : 'transparent',
        borderLeft: isActive ? '3px solid #93c5fd' : '3px solid transparent'
      })}
    >
      {label}
    </NavLink>
  )
}
