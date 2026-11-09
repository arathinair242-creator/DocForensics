import { useState, useEffect } from 'react'
import { BookOpen, FileText } from 'lucide-react'
import api from '../services/api'
import { generateAndDownloadDossier } from '../services/dossier'

export default function Dossiers() {
  const [investigations, setInvestigations] = useState([])
  const [generating, setGenerating] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/investigations/').then(r => setInvestigations(r.data)).finally(() => setLoading(false))
  }, [])

  const generate = async (invId) => {
    setGenerating(g => ({ ...g, [invId]: true }))
    try {
      await generateAndDownloadDossier(invId)
    } catch(e) { alert('Generation failed: ' + (e.response?.data?.detail || e.message)) }
    finally { setGenerating(g => ({ ...g, [invId]: false })) }
  }

  if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div><h2>Investigation Dossiers</h2><p>Generate and download professional PDF investigation reports</p></div>
      </div>
      <div className="alert alert-info" style={{ marginBottom:20 }}>
        <BookOpen size={14} style={{ flexShrink:0, marginTop:1 }} />
        Dossiers are generated from actual investigation findings. Generate a dossier after completing document analysis and anomaly review.
      </div>
      {investigations.length === 0 ? (
        <div className="empty-state"><BookOpen size={40} /><h4>No investigations found</h4><p>Create an investigation first to generate a dossier.</p></div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {investigations.map(inv => (
            <div key={inv.id} className="card">
              <div style={{ padding:'16px 20px', display:'flex', alignItems:'center', gap:14 }}>
                <div style={{ width:44, height:44, background:'rgba(168,85,247,0.2)', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, border:'1px solid rgba(168,85,247,0.35)' }}>
                  <BookOpen size={20} color="#FFFFFF" />
                </div>
                <div style={{ flex:1 }}>
                  <div style={{ fontWeight:800, fontSize:15, color:'#FFFFFF' }}>INV-{String(inv.id).padStart(4,'0')} — {inv.name}</div>
                  <div style={{ fontSize:12, color:'#D8B4FE', marginTop:3 }}>
                    {inv.document_count} documents · {inv.anomaly_count} anomalies ·
                    Status: <span className={`badge badge-${inv.status === 'completed' ? 'green' : inv.status === 'in_progress' ? 'orange' : 'grey'}`} style={{ fontSize:10 }}>{inv.status}</span>
                  </div>
                </div>
                <div style={{ display:'flex', gap:8 }}>
                  <button className="btn btn-primary" onClick={() => generate(inv.id)} disabled={generating[inv.id]} id={`btn-generate-${inv.id}`}>
                    {generating[inv.id] ? <><span className="spinner" style={{ width:14, height:14 }} /> Generating…</> : <><FileText size={14} /> Generate &amp; Download PDF</>}
                  </button>
                </div>
              </div>
              {inv.description && (
                <div style={{ padding:'10px 20px 14px', fontSize:13, color:'#F3E8FF', borderTop:'1px solid var(--border)' }}>{inv.description.slice(0,150)}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
