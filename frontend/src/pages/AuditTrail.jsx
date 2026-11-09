import { useState, useEffect } from 'react'
import { ClipboardList, Activity } from 'lucide-react'
import api from '../services/api'

function timeAgo(ts) {
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return new Date(ts).toLocaleDateString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' })
}

const ACTIVITY_COLORS = {
  'Investigation Created': '#27AE60',
  'Document Uploaded': '#3498DB',
  'OCR Completed': '#9B59B6',
  'Document Classified': '#8E44AD',
  'Visual Forensics Completed': '#E67E22',
  'Processing Completed': '#27AE60',
  'Processing Error': '#C0392B',
  'Anomaly Updated': '#F39C12',
  'Cross-Document Correlation Completed': '#1ABC9C',
  'Dossier Generated': '#0D2137',
  'Demo Investigation Created': '#3498DB',
}

export default function AuditTrail() {
  const [logs, setLogs] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/audit/').then(r => setLogs(r.data)).finally(() => setLoading(false))
    const t = setInterval(() => api.get('/audit/').then(r => setLogs(r.data)), 15000)
    return () => clearInterval(t)
  }, [])

  const filtered = filter ? logs.filter(l => l.activity?.toLowerCase().includes(filter.toLowerCase()) ||
    l.details?.toLowerCase().includes(filter.toLowerCase()) || l.investigation_name?.toLowerCase().includes(filter.toLowerCase())) : logs

  if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div><h2>Audit Trail</h2><p>Complete, tamper-evident log of all platform activities</p></div>
        <div style={{ fontSize:12, color:'var(--text-med)' }}>{filtered.length} entries</div>
      </div>

      <div className="card" style={{ marginBottom:16, padding:'12px 16px' }}>
        <input className="form-control" placeholder="Filter by activity, details, or investigation name…" value={filter} onChange={e => setFilter(e.target.value)} id="audit-filter" />
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state"><ClipboardList size={40} /><h4>No audit records</h4><p>Activities will appear here as investigations are created and processed.</p></div>
      ) : (
        <div className="card">
          <div style={{ position:'relative' }}>
            {filtered.map((log, i) => {
              const color = ACTIVITY_COLORS[log.activity] || '#8A9BB0'
              return (
                <div key={log.id || i} style={{ display:'flex', gap:14, padding:'12px 20px', borderBottom: i < filtered.length-1 ? '1px solid var(--border)' : 'none', alignItems:'flex-start' }}>
                  <div style={{ display:'flex', flexDirection:'column', alignItems:'center', paddingTop:4 }}>
                    <div style={{ width:10, height:10, borderRadius:'50%', background:color, flexShrink:0 }} />
                    {i < filtered.length-1 && <div style={{ width:1, height:'100%', background:'var(--border)', marginTop:4, minHeight:20 }} />}
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap', marginBottom:2 }}>
                      <span style={{ fontWeight:800, fontSize:13, color:'#FFFFFF' }}>{log.activity}</span>
                      {log.investigation_name && (
                        <span className="badge badge-navy" style={{ fontSize:10 }}>{log.investigation_name?.slice(0,30)}</span>
                      )}
                    </div>
                    {log.details && <div style={{ fontSize:13, color:'#F3E8FF', marginBottom:3 }}>{log.details}</div>}
                    <div style={{ display:'flex', gap:12, fontSize:11, color:'#D8B4FE' }}>
                      <span>By: {log.user_name}</span>
                      {log.document_name && <span>Doc: {log.document_name}</span>}
                      <span style={{ marginLeft:'auto' }}>{timeAgo(log.timestamp)}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
