import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

export default function AuthPage() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = field => e => setForm(f => ({ ...f, [field]: e.target.value }))

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        if (!form.name.trim()) { setError('Please enter your name'); setLoading(false); return }
        await register(form.name, form.email, form.password)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <div style={styles.logoMark} />
          <span style={styles.logoText}>EmoAgent</span>
        </div>
        <h1 style={styles.heading}>
          {mode === 'login' ? 'Welcome back' : 'Start your journey'}
        </h1>
        <p style={styles.sub}>
          {mode === 'login'
            ? 'A safe space to talk, reflect, and feel heard.'
            : 'Empathetic conversations, whenever you need them.'}
        </p>

        <form onSubmit={submit} style={styles.form}>
          {mode === 'register' && (
            <div style={styles.field}>
              <label style={styles.label}>Your name</label>
              <input
                style={styles.input}
                type="text"
                placeholder="How should I call you?"
                value={form.name}
                onChange={handle('name')}
                autoFocus
              />
            </div>
          )}
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              style={styles.input}
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={handle('email')}
              autoFocus={mode === 'login'}
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              placeholder={mode === 'login' ? '••••••••' : 'At least 8 characters'}
              value={form.password}
              onChange={handle('password')}
            />
          </div>

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" style={styles.btn} disabled={loading}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p style={styles.toggle}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            style={styles.link}
            onClick={() => { setMode(m => m === 'login' ? 'register' : 'login'); setError('') }}
          >
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>

        <p style={styles.disclaimer}>
          EmoAgent is a wellness companion, not a medical service. In a crisis, please contact a professional.
        </p>
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
    background: 'var(--warm)',
  },
  card: {
    width: '100%',
    maxWidth: 420,
    background: 'var(--white)',
    borderRadius: 20,
    padding: '2.5rem',
    boxShadow: 'var(--shadow)',
    border: '1px solid var(--warm-mid)',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: '1.75rem',
  },
  logoMark: {
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: 'var(--sage)',
  },
  logoText: {
    fontFamily: "'DM Serif Display', serif",
    fontSize: 20,
    color: 'var(--ink)',
    letterSpacing: '-0.02em',
  },
  heading: {
    fontFamily: "'DM Serif Display', serif",
    fontSize: 28,
    fontWeight: 400,
    color: 'var(--ink)',
    marginBottom: '0.5rem',
    letterSpacing: '-0.02em',
  },
  sub: {
    fontSize: 14,
    color: 'var(--ink-soft)',
    marginBottom: '1.75rem',
    lineHeight: 1.5,
  },
  form: { display: 'flex', flexDirection: 'column', gap: '1rem' },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 13, fontWeight: 500, color: 'var(--ink-mid)' },
  input: {
    padding: '10px 14px',
    borderRadius: 'var(--radius-sm)',
    border: '1.5px solid var(--warm-mid)',
    fontSize: 15,
    background: 'var(--warm)',
    color: 'var(--ink)',
    outline: 'none',
    transition: 'border-color 0.15s',
    fontFamily: 'inherit',
  },
  error: {
    fontSize: 13,
    color: 'var(--danger)',
    background: 'var(--danger-bg)',
    padding: '8px 12px',
    borderRadius: 'var(--radius-sm)',
  },
  btn: {
    marginTop: 4,
    padding: '12px',
    background: 'var(--sage)',
    color: 'var(--white)',
    border: 'none',
    borderRadius: 'var(--radius-sm)',
    fontSize: 15,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'opacity 0.15s',
  },
  toggle: {
    marginTop: '1.25rem',
    textAlign: 'center',
    fontSize: 14,
    color: 'var(--ink-soft)',
  },
  link: {
    background: 'none',
    border: 'none',
    color: 'var(--sage)',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    fontFamily: 'inherit',
  },
  disclaimer: {
    marginTop: '1.5rem',
    fontSize: 12,
    color: 'var(--ink-soft)',
    textAlign: 'center',
    lineHeight: 1.5,
    borderTop: '1px solid var(--warm-mid)',
    paddingTop: '1.25rem',
  }
}
