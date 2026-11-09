import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ email: '', password: '', fullName: '' })
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const { login, register, googleLogin } = useAuth()
  const navigate = useNavigate()

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const validate = () => {
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) return 'Enter a valid email address'
    if (form.password.length < 6) return 'Password must be at least 6 characters'
    if (mode === 'register' && !form.fullName.trim()) return 'Full name is required'
    return null
  }

  const handleSubmit = async e => {
    e.preventDefault()
    const err = validate()
    if (err) return setError(err)
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') await login(form.email, form.password)
      else await register(form.email, form.fullName, form.password)
      navigate('/')
    } catch (ex) {
      setError(ex.response?.data?.detail || 'Authentication failed. Please verify credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    setGoogleLoading(true)
    setError('')
    try {
      await googleLogin(credentialResponse.credential)
      navigate('/')
    } catch (ex) {
      setError(ex.message || 'Google authentication failed. Please try again.')
    } finally {
      setGoogleLoading(false)
    }
  }

  const handleGoogleError = () => setError('Google sign-in was cancelled or encountered an error.')

  const features = [
    {
      num: '01',
      title: 'AI-Powered OCR',
      desc: 'Extract text from documents with high accuracy.',
    },
    {
      num: '02',
      title: 'Visual Forensics',
      desc: 'Detect image tampering and manipulation using OpenCV.',
    },
    {
      num: '03',
      title: 'Cross-Document AI',
      desc: 'Correlate evidence across document collections.',
    },
    {
      num: '04',
      title: 'PDF Dossiers',
      desc: 'Generate professional investigation reports.',
    },
  ]

  return (
    <div className="login-container">
      {/* ── Left Editorial Hero Section ────────── */}
      <div className="login-editorial">
        <div className="editorial-inner">
          {/* Typography-Led Brand Header */}
          <div className="editorial-brand">
            <span className="brand-badge">DF-INTEL</span>
            <div className="brand-title">
              Doc<span className="brand-accent">Forensics</span>
            </div>
            <div className="brand-sub">Enterprise Forensic Intelligence Platform</div>
          </div>

          {/* Controlled Editorial Headline */}
          <div className="editorial-hero">
            <h1 className="hero-headline">
              Forensic document intelligence for enterprise investigations.
            </h1>
            <p className="hero-desc">
              Scientific-grade analytical software engineered to detect structural manipulation,
              forged metadata, and cross-document inconsistencies across institutional archives.
            </p>
          </div>

          {/* Clean Typography-Led Features with Subtle Visual Separators */}
          <div className="editorial-features">
            {features.map((item) => (
              <div key={item.num} className="feature-item">
                <span className="feature-index">{item.num}</span>
                <div className="feature-content">
                  <div className="feature-title">{item.title}</div>
                  <div className="feature-desc">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Refined Enterprise Metrics Bar */}
          <div className="editorial-metrics">
            <div className="metric-box">
              <span className="metric-val">99.2%</span>
              <span className="metric-lbl">Extraction Precision</span>
            </div>
            <div className="metric-divider" />
            <div className="metric-box">
              <span className="metric-val">OpenCV</span>
              <span className="metric-lbl">Forensics Engine</span>
            </div>
            <div className="metric-divider" />
            <div className="metric-box">
              <span className="metric-val">ISO 27001</span>
              <span className="metric-lbl">Audit Integrity</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Authentication Panel ──────────── */}
      <div className="login-panel">
        <div className="panel-inner">
          <div className="auth-card">
            {/* Header */}
            <div className="auth-header">
              <h2 className="auth-title">
                {mode === 'login' ? 'Platform Authentication' : 'Create Investigator Account'}
              </h2>
              <p className="auth-subtitle">
                {mode === 'login'
                  ? 'Enter your institutional credentials to access the console'
                  : 'Register authorized investigator credentials'}
              </p>
            </div>

            {/* Restrained Tab Toggle */}
            <div className="auth-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'login'}
                onClick={() => { setMode('login'); setError('') }}
                className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
              >
                Sign In
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'register'}
                onClick={() => { setMode('register'); setError('') }}
                className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
              >
                Register
              </button>
            </div>

            {/* Google OAuth Section */}
            <div className="auth-google-wrap">
              {googleLoading ? (
                <div className="google-loading-state">
                  <span className="spinner" />
                  <span>Verifying Google token...</span>
                </div>
              ) : (
                <div className="google-btn-container">
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={handleGoogleError}
                    theme="filled_black"
                    size="large"
                    shape="rectangular"
                    width="100%"
                    text={mode === 'login' ? 'signin_with' : 'signup_with'}
                  />
                </div>
              )}
            </div>

            {/* Restrained Line Divider */}
            <div className="auth-divider">
              <span className="divider-line" />
              <span className="divider-text">or continue with email</span>
              <span className="divider-line" />
            </div>

            {/* Error Message */}
            {error && (
              <div className="auth-error-alert" role="alert">
                <AlertCircle size={15} className="error-icon" />
                <span>{error}</span>
              </div>
            )}

            {/* Credentials Form */}
            <form onSubmit={handleSubmit} className="auth-form" noValidate>
              {mode === 'register' && (
                <div className="auth-field">
                  <label htmlFor="input-fullName" className="field-label">Full Name</label>
                  <input
                    id="input-fullName"
                    name="fullName"
                    type="text"
                    value={form.fullName}
                    onChange={handleChange}
                    placeholder="e.g. Dr. Arthur Vance"
                    className="field-input"
                    autoComplete="name"
                    required
                  />
                </div>
              )}

              <div className="auth-field">
                <label htmlFor="input-email" className="field-label">Institutional Email</label>
                <input
                  id="input-email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="analyst@docforensics.ai"
                  className="field-input"
                  autoComplete="email"
                  required
                />
              </div>

              <div className="auth-field">
                <div className="field-label-row">
                  <label htmlFor="input-password" className="field-label">Password</label>
                  {mode === 'login' && (
                    <span className="field-helper">Minimum 6 characters</span>
                  )}
                </div>
                <div className="field-input-group">
                  <input
                    id="input-password"
                    name="password"
                    type={showPass ? 'text' : 'password'}
                    value={form.password}
                    onChange={handleChange}
                    placeholder="••••••••••••"
                    className="field-input pass-input"
                    autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                    required
                  />
                  <button
                    type="button"
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPass(s => !s)}
                    className="field-toggle-pass"
                  >
                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="auth-submit-btn"
              >
                {loading && <span className="spinner" style={{ borderTopColor: '#080E19' }} />}
                <span>{mode === 'login' ? 'Sign In to Platform' : 'Complete Registration'}</span>
              </button>
            </form>

            {/* Mode Switch */}
            <div className="auth-switch">
              <span className="switch-text">
                {mode === 'login' ? 'New investigator?' : 'Already have credentials?'}
              </span>
              <button
                type="button"
                onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
                className="switch-action"
              >
                {mode === 'login' ? 'Create an account' : 'Sign in'}
              </button>
            </div>
          </div>

          {/* Enterprise Disclaimer Footer */}
          <div className="auth-security-notice">
            <span className="security-status-indicator" />
            <span>Classified enterprise environment. All system activities are audited and cryptographically verified.</span>
          </div>
        </div>
      </div>

      <style>{`
        /* ── Container Layout ─────────────────── */
        .login-container {
          min-height: 100vh;
          display: flex;
          background: #080E19;
          color: #F1F5F9;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          position: relative;
        }

        /* ── Left Editorial Hero Section ──────── */
        .login-editorial {
          flex: 1.15;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 64px 72px;
          background: #080E19;
          border-right: 1px solid #25364A;
          position: relative;
        }

        .editorial-inner {
          max-width: 540px;
          width: 100%;
        }

        /* ── Brand ────────────────────────────── */
        .editorial-brand {
          margin-bottom: 48px;
        }

        .brand-badge {
          display: inline-block;
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.8px;
          color: #13B8D5;
          background: rgba(19, 184, 213, 0.08);
          border: 1px solid rgba(19, 184, 213, 0.25);
          padding: 3px 8px;
          border-radius: 4px;
          margin-bottom: 12px;
        }

        .brand-title {
          font-size: 26px;
          font-weight: 700;
          color: #F1F5F9;
          letter-spacing: -0.6px;
          line-height: 1.1;
        }

        .brand-accent {
          color: #13B8D5;
        }

        .brand-sub {
          font-size: 12px;
          font-weight: 500;
          color: #64748B;
          letter-spacing: 0.5px;
          text-transform: uppercase;
          margin-top: 6px;
        }

        /* ── Hero Copy ────────────────────────── */
        .editorial-hero {
          margin-bottom: 44px;
        }

        .hero-headline {
          font-size: 32px;
          font-weight: 700;
          line-height: 1.25;
          color: #F1F5F9;
          letter-spacing: -0.8px;
          margin-bottom: 16px;
        }

        .hero-desc {
          font-size: 14.5px;
          line-height: 1.65;
          color: #9CAFC4;
          font-weight: 400;
        }

        /* ── Features List ────────────────────── */
        .editorial-features {
          display: flex;
          flex-direction: column;
          border-top: 1px solid #25364A;
          margin-bottom: 44px;
        }

        .feature-item {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          padding: 16px 0;
          border-bottom: 1px solid #25364A;
        }

        .feature-index {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          font-weight: 600;
          color: #13B8D5;
          padding-top: 2px;
          width: 22px;
          flex-shrink: 0;
        }

        .feature-content {
          flex: 1;
        }

        .feature-title {
          font-size: 13.5px;
          font-weight: 600;
          color: #F1F5F9;
          margin-bottom: 2px;
          letter-spacing: -0.1px;
        }

        .feature-desc {
          font-size: 12.5px;
          line-height: 1.5;
          color: #9CAFC4;
        }

        /* ── Metrics ──────────────────────────── */
        .editorial-metrics {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .metric-box {
          display: flex;
          flex-direction: column;
        }

        .metric-val {
          font-family: 'JetBrains Mono', monospace;
          font-size: 16px;
          font-weight: 700;
          color: #F1F5F9;
          letter-spacing: -0.3px;
        }

        .metric-lbl {
          font-size: 11px;
          color: #64748B;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-top: 2px;
        }

        .metric-divider {
          width: 1px;
          height: 28px;
          background: #25364A;
        }

        /* ── Right Panel ──────────────────────── */
        .login-panel {
          flex: 0.95;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px 56px;
          background: #0D1625;
        }

        .panel-inner {
          max-width: 420px;
          width: 100%;
        }

        .auth-card {
          background: #111C2D;
          border: 1px solid #25364A;
          border-radius: 8px;
          padding: 32px 30px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }

        .auth-header {
          margin-bottom: 22px;
        }

        .auth-title {
          font-size: 18px;
          font-weight: 700;
          color: #F1F5F9;
          letter-spacing: -0.3px;
          margin-bottom: 5px;
        }

        .auth-subtitle {
          font-size: 12.5px;
          color: #9CAFC4;
          line-height: 1.45;
        }

        /* ── Tabs ─────────────────────────────── */
        .auth-tabs {
          display: flex;
          gap: 2px;
          background: #080E19;
          padding: 3px;
          border-radius: 6px;
          border: 1px solid #25364A;
          margin-bottom: 20px;
        }

        .auth-tab {
          flex: 1;
          padding: 7px 0;
          border: none;
          background: transparent;
          color: #9CAFC4;
          font-size: 12.5px;
          font-weight: 500;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.15s ease-in-out;
          font-family: inherit;
        }

        .auth-tab.active {
          background: #111C2D;
          color: #F1F5F9;
          font-weight: 600;
          border: 1px solid #25364A;
        }

        .auth-tab:not(.active):hover {
          color: #F1F5F9;
        }

        /* ── Google Section ──────────────────── */
        .auth-google-wrap {
          margin-bottom: 18px;
        }

        .google-loading-state {
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          font-size: 12.5px;
          color: #9CAFC4;
          background: #080E19;
          border: 1px solid #25364A;
          border-radius: 6px;
        }

        .google-btn-container {
          width: 100%;
          display: flex;
          justify-content: center;
        }

        /* ── Divider ──────────────────────────── */
        .auth-divider {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 18px;
        }

        .divider-line {
          flex: 1;
          height: 1px;
          background: #25364A;
        }

        .divider-text {
          font-size: 11px;
          color: #64748B;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 500;
          white-space: nowrap;
        }

        /* ── Error Alert ──────────────────────── */
        .auth-error-alert {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 10px 12px;
          background: rgba(220, 38, 38, 0.1);
          border: 1px solid rgba(220, 38, 38, 0.35);
          border-radius: 6px;
          margin-bottom: 16px;
          color: #F87171;
          font-size: 12.5px;
          line-height: 1.45;
        }

        .error-icon {
          flex-shrink: 0;
          margin-top: 1px;
          color: #F87171;
        }

        /* ── Form Fields ──────────────────────── */
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .auth-field {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .field-label-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .field-label {
          font-size: 11px;
          font-weight: 600;
          color: #9CAFC4;
          letter-spacing: 0.4px;
          text-transform: uppercase;
        }

        .field-helper {
          font-size: 11px;
          color: #64748B;
        }

        .field-input {
          width: 100%;
          padding: 9px 12px;
          background: #080E19;
          border: 1px solid #25364A;
          border-radius: 6px;
          color: #F1F5F9;
          font-size: 13.5px;
          font-family: inherit;
          transition: border-color 0.15s ease-in-out;
          outline: none;
        }

        .field-input:focus {
          border-color: #13B8D5;
          background: #0B1220;
        }

        .field-input::placeholder {
          color: #64748B;
        }

        .field-input-group {
          position: relative;
        }

        .pass-input {
          padding-right: 38px;
        }

        .field-toggle-pass {
          position: absolute;
          right: 10px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: #64748B;
          cursor: pointer;
          padding: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: color 0.15s;
        }

        .field-toggle-pass:hover {
          color: #9CAFC4;
        }

        /* ── Submit Button ────────────────────── */
        .auth-submit-btn {
          width: 100%;
          padding: 10px 16px;
          background: #13B8D5;
          color: #080E19;
          border: 1px solid #13B8D5;
          border-radius: 6px;
          font-size: 13.5px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 4px;
          transition: background-color 0.15s, border-color 0.15s;
          font-family: inherit;
        }

        .auth-submit-btn:hover:not(:disabled) {
          background: #38BDF8;
          border-color: #38BDF8;
        }

        .auth-submit-btn:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        /* ── Switch Action ────────────────────── */
        .auth-switch {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          margin-top: 18px;
          font-size: 12.5px;
        }

        .switch-text {
          color: #64748B;
        }

        .switch-action {
          background: none;
          border: none;
          color: #13B8D5;
          font-weight: 600;
          cursor: pointer;
          font-size: 12.5px;
          padding: 0;
          font-family: inherit;
        }

        .switch-action:hover {
          color: #38BDF8;
          text-decoration: underline;
        }

        /* ── Security Notice ──────────────────── */
        .auth-security-notice {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-top: 20px;
          font-size: 11px;
          line-height: 1.45;
          color: #64748B;
        }

        .security-status-indicator {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #16A34A;
          flex-shrink: 0;
          margin-top: 4px;
        }

        /* ── Responsive ───────────────────────── */
        @media (max-width: 960px) {
          .login-container {
            flex-direction: column;
          }
          .login-editorial {
            border-right: none;
            border-bottom: 1px solid #25364A;
            padding: 44px 28px;
          }
          .login-panel {
            padding: 44px 24px;
          }
        }
      `}</style>
    </div>
  )
}
