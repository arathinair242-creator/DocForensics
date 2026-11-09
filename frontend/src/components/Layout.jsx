import { Outlet, useLocation, useNavigate, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Plus, FileText, History, AlertTriangle,
  Search, BookOpen, ClipboardList, Settings, LogOut, NotebookPen
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Overview', end: true },
  { to: '/new-investigation', icon: Plus, label: 'New Investigation' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/history', icon: History, label: 'Investigation History' },
  { to: '/anomalies', icon: AlertTriangle, label: 'Anomaly Analysis' },
  { to: '/journal', icon: NotebookPen, label: 'Investigation Journal' },
  { to: '/evidence', icon: Search, label: 'Evidence Explorer' },
  { to: '/dossiers', icon: BookOpen, label: 'Investigation Dossiers' },
  { to: '/audit', icon: ClipboardList, label: 'Audit Trail' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

const PAGE_TITLES = {
  '/': 'Overview',
  '/new-investigation': 'New Investigation',
  '/documents': 'Documents',
  '/history': 'Investigation History',
  '/anomalies': 'Anomaly Analysis',
  '/journal': 'Investigation Journal',
  '/evidence': 'Evidence Explorer',
  '/dossiers': 'Investigation Dossiers',
  '/audit': 'Audit Trail',
  '/settings': 'Settings',
}

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const title = Object.entries(PAGE_TITLES).sort((a, b) => b[0].length - a[0].length)
    .find(([path]) => location.pathname.startsWith(path))?.[1] || 'DocForensics'

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-wrapper">
            <div className="brand-symbol">
              <span className="brand-symbol-dot" />
            </div>
            <div className="brand-typography">
              <div className="brand-name">Doc<span>Forensics</span></div>
              <div className="brand-tagline">Intelligence Platform</div>
            </div>
          </div>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}>
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="sidebar-nav-item" onClick={handleLogout}>
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="main-content">
        <header className="topbar">
          <span className="topbar-title">{title}</span>
          <div className="topbar-right">
            <div className="user-badge">
              <div className="avatar">{user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}</div>
              <span>{user?.full_name || user?.email}</span>
            </div>
          </div>
        </header>
        <main className="page-content fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
