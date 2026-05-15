import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login }   = useAuth()
  const navigate    = useNavigate()

  const [form, setForm] = useState({ username: '', password: '' })
  const [errors, setErrors] = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw] = useState(false)

  function validate() {
    const e = {}
    if (!form.username.trim()) e.username = 'Username is required'
    if (form.password.length < 8) e.password = 'Password must be at least 8 characters'
    return e
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setApiError('')
    const e2 = validate()
    if (Object.keys(e2).length) { setErrors(e2); return }
    setErrors({})
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/search')
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Invalid credentials'
      setApiError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="card auth-card">

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--brand)', display: 'inline-block' }} />
            <span style={{ fontFamily: "'Source Serif 4', serif", fontSize: '22px', fontWeight: 600, color: 'var(--text-primary)' }}>
              DealMiner
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            Sign in to continue
          </p>
        </div>

        {/* API Error */}
        {apiError && (
          <div className="toast toast-error" style={{ marginBottom: '20px', animation: 'none', position: 'static' }}>
            <span>✕</span> {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              className={`form-input ${errors.username ? 'error' : ''}`}
              placeholder="your_username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              autoComplete="username"
            />
            {errors.username && <span className="form-error">⚠ {errors.username}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-password"
                type={showPw ? 'text' : 'password'}
                className={`form-input ${errors.password ? 'error' : ''}`}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                autoComplete="current-password"
                style={{ paddingRight: '44px' }}
              />
              <button
                type="button"
                onClick={() => setShowPw(!showPw)}
                style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && <span className="form-error">⚠ {errors.password}</span>}
          </div>

          <button
            id="login-submit"
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
          >
            {loading ? <><span className="spinner" /> Signing in…</> : <><LogIn size={15} /> Sign In</>}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <div className="divider" style={{ marginBottom: '20px' }} />
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: 'var(--brand)', fontWeight: 500 }}>
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
