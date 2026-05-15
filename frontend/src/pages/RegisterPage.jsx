import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, UserPlus } from 'lucide-react'
import { authApi } from '../api/auth'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm_password: '' })
  const [errors, setErrors] = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw]   = useState(false)

  function validate() {
    const e = {}
    if (!form.username.trim())     e.username = 'Username is required'
    if (!form.email.trim())        e.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Enter a valid email'
    if (form.password.length < 8)  e.password = 'Password must be at least 8 characters'
    if (form.password !== form.confirm_password) e.confirm_password = 'Passwords do not match'
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
      await authApi.register(form)
      navigate('/login')
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [field, msgs] of Object.entries(data)) {
        mapped[field] = Array.isArray(msgs) ? msgs[0] : msgs
      }
      if (Object.keys(mapped).length === 0) {
        setApiError(err.response?.data?.detail || err.message || 'Failed to register. Please try again.')
      } else {
        setErrors(mapped)
      }
    } finally {
      setLoading(false)
    }
  }

  const field = (name, label, type = 'text', placeholder = '', opts = {}) => (
    <div className="form-group">
      <label className="form-label" htmlFor={`reg-${name}`}>{label}</label>
      <div style={{ position: 'relative' }}>
        <input
          id={`reg-${name}`}
          type={opts.isPw ? (showPw ? 'text' : 'password') : type}
          className={`form-input ${errors[name] ? 'error' : ''}`}
          placeholder={placeholder}
          value={form[name]}
          onChange={(e) => setForm({ ...form, [name]: e.target.value })}
          autoComplete={opts.autoComplete}
          style={opts.isPw ? { paddingRight: '44px' } : {}}
        />
        {opts.isPw && (
          <button type="button" onClick={() => setShowPw(!showPw)}
            style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}>
            {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {errors[name] && <span className="form-error">⚠ {errors[name]}</span>}
    </div>
  )

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--brand)', display: 'inline-block' }} />
            <span style={{ fontFamily: "'Source Serif 4', serif", fontSize: '22px', fontWeight: 600, color: 'var(--text-primary)' }}>
              DealMiner
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Create your account</p>
        </div>

        {apiError && (
          <div className="toast toast-error" style={{ marginBottom: '16px', animation: 'none', position: 'static' }}>
            <span>✕</span> {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {field('username', 'Username', 'text', 'your_username', { autoComplete: 'username' })}
          {field('email',    'Email',    'email', 'you@example.com', { autoComplete: 'email' })}
          {field('password', 'Password', 'password', '••••••••', { isPw: true, autoComplete: 'new-password' })}
          {field('confirm_password', 'Confirm Password', 'password', '••••••••', { isPw: true, autoComplete: 'new-password' })}

          <button
            id="register-submit"
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
          >
            {loading ? <><span className="spinner" /> Creating account…</> : <><UserPlus size={15} /> Create Account</>}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <div className="divider" style={{ marginBottom: '20px' }} />
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--brand)', fontWeight: 500 }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
