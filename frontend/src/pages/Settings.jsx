import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Settings as SettingsIcon, User, Lock, Info, LogOut, Shield } from 'lucide-react'

export default function Settings() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <div className="fade-in" style={{ maxWidth: 640 }}>
      <div className="page-header">
        <div><h2>Settings</h2><p>Account and platform configuration</p></div>
      </div>

      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-header"><h3>Account Information</h3></div>
        <div className="card-body">
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input className="form-control" value={user?.full_name || ''} readOnly style={{ background:'var(--bg-input)' }} />
          </div>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input className="form-control" value={user?.email || ''} readOnly style={{ background:'var(--bg-input)' }} />
          </div>
          <div className="form-group">
            <label className="form-label">User ID</label>
            <input className="form-control" value={`USR-${String(user?.user_id || '').padStart(4,'0')}`} readOnly style={{ background:'var(--bg-input)' }} />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-header"><h3>Platform Configuration</h3></div>
        <div className="card-body">
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {[
              ['Backend API', 'http://localhost:8000', 'Connected'],
              ['AI / LLM Reasoning', 'OpenAI gpt-4o-mini (configured in .env) with local fallback', 'Active'],
              ['OCR Engine', 'Tesseract OCR + PyMuPDF', 'Active'],
              ['Vision Analysis', 'OpenCV 4.x — ELA, Noise, Edge Detection', 'Active'],
              ['Classification', 'Keyword-weighted document classifier (9 types)', 'Active'],
              ['Database', 'SQLite (docforensics.db)', 'Active'],
              ['Report Format', 'ReportLab PDF — A4, 6 sections', 'Active'],
            ].map(([key, val, status]) => (
              <div key={key} style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 0', borderBottom:'1px solid var(--border)' }}>
                <div style={{ flex:'0 0 180px', fontSize:13, fontWeight:700, color:'#FFFFFF' }}>{key}</div>
                <div style={{ flex:1, fontSize:12, color:'#D8B4FE' }}>{val}</div>
                <span className="badge badge-green" style={{ fontSize:10 }}>{status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-header"><h3>Important Disclaimer</h3></div>
        <div className="card-body">
          <div className="alert alert-warning">
            <Shield size={15} style={{ flexShrink:0, marginTop:2 }} />
            <div style={{ fontSize:12 }}>
              <strong>Authorized Investigation Tool Only.</strong> This platform is designed for certified document investigators. All findings are AI-generated observations that require human expert review. No automated finding constitutes legal evidence. All activities are recorded in the audit trail. Unauthorized use is strictly prohibited.
            </div>
          </div>
        </div>
      </div>

      <button className="btn btn-danger" onClick={() => { logout(); navigate('/login') }} style={{ display:'flex', alignItems:'center', gap:6 }}>
        <LogOut size={15} /> Sign Out of Platform
      </button>
    </div>
  )
}
