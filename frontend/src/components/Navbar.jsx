import { NavLink, useNavigate } from 'react-router-dom'
import { Search, History, LogOut, BarChart3 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import AlertBell from './AlertBell'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate         = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      {/* Brand */}
      <NavLink to="/search" className="navbar-brand">
        <span className="navbar-brand-dot" />
        PriceScope
      </NavLink>

      {/* Nav links */}
      <div className="navbar-links">
        <NavLink
          to="/search"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <Search size={14} />
          <span>Search</span>
        </NavLink>

        <NavLink
          to="/history"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <History size={14} />
          <span>History</span>
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <BarChart3 size={14} />
          <span>Analytics</span>
        </NavLink>
      </div>

      {/* Bell + User area */}
      <div className="navbar-user">
        <AlertBell />
        {user?.username && (
          <span className="navbar-username">{user.username}</span>
        )}
        <button className="btn btn-ghost btn-sm" onClick={handleLogout} title="Logout">
          <LogOut size={14} />
          <span>Sign out</span>
        </button>
      </div>
    </nav>
  )
}

