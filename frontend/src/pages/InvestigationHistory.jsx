import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { History, AlertTriangle, FileText, BookOpen, Eye } from 'lucide-react'
import api from '../services/api'

export default function InvestigationHistory() {
  const [investigations, setInvestigations] = useState([])
  const [loading, setLoading] = useState(true)
  const [updatingStatus, setUpdatingStatus] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/investigations/').then(r => setInvestigations(r.data)).finally(() => setLoading(false))
  }, [])

  const updateStatus = async (invId, status) => {
    setUpdatingStatus(u => ({ ...u, [invId]: true }))
    try {
      await api.patch(`/investigations/${invId}/status?new_status=${status}`)
      setInvestigations(prev => prev.map(i => i.id === invId ? { ...i, status } : i))
    } catch(e) { alert('Update failed') }
    finally { setUpdatingStatus(u => ({ ...u, [invId]: false })) }
  }

  if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div><h2>Investigation History</h2><p>All investigations created on this platform</p></div>
        <span style={{ fontSize:13, color:'var(--text-med)' }}>{investigations.length} investigation(s)</span>
      </div>

      {investigations.length === 0 ? (
        <div className="empty-state"><History size={40} /><h4>No investigations yet</h4><p>Create your first investigation to get started.</p></div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {investigations.map(inv => (
            <div key={inv.id} className="card">
              <div style={{ padding:'16px 20px', display:'flex', alignItems:'flex-start', gap:14 }}>
                <div style={{ width:44, height:44, background:'var(--bg-input)', borderRadius:10, border:'1px solid var(--border-light)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, fontWeight:800, fontSize:12, color:'#FFFFFF' }}>
                  {String(inv.id).padStart(4,'0')}
                </div>
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ fontWeight:800, fontSize:15, color:'#FFFFFF', marginBottom:4 }}>{inv.name}</div>
                  {inv.description && (
                    <div style={{ fontSize:13, color:'#D8B4FE', marginBottom:8 }}>{inv.description.slice(0,120)}</div>
                  )}
                  <div style={{ display:'flex', gap:16, flexWrap:'wrap', fontSize:12, color:'#C084FC' }}>
                    <span style={{ display:'flex', alignItems:'center', gap:4 }}><FileText size={12} />{inv.document_count} document(s)</span>
                    <span style={{ display:'flex', alignItems:'center', gap:4 }}><AlertTriangle size={12} />{inv.anomaly_count} anomaly(ies)</span>
                    <span style={{ color:'#D8B4FE' }}>Created: {new Date(inv.created_at).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })}</span>
                  </div>
                </div>
                <div style={{ display:'flex', flexDirection:'column', gap:8, alignItems:'flex-end' }}>
                  <select className="form-control" value={inv.status}
                    onChange={e => updateStatus(inv.id, e.target.value)}
                    disabled={updatingStatus[inv.id]}
                    style={{ width:160, fontSize:12, padding:'4px 8px' }}>
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="closed">Closed</option>
                  </select>
                  <div style={{ display:'flex', gap:6 }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/anomalies/${inv.id}`)}>
                      <AlertTriangle size={12} /> Anomalies
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/evidence`)}>
                      <Eye size={12} /> Evidence
                    </button>
                    <button className="btn btn-primary btn-sm" onClick={() => navigate(`/dossiers`)}>
                      <BookOpen size={12} /> Dossier
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
