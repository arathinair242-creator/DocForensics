import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AlertTriangle, Filter, Edit3, CheckCircle, FileText, NotebookPen } from 'lucide-react'
import api from '../services/api'
import { generateAndDownloadDossier } from '../services/dossier'

const SEV_MAP = { Critical: 'sev-critical', High: 'sev-high', Medium: 'sev-medium', Low: 'sev-low' }
const STATUS_LABELS = {
  detected: 'Detected',
  verified_observation: 'Verified Observation',
  requires_investigation: 'Requires Investigation',
  false_positive: 'False Positive'
}

function AnomalyRow({ anomaly, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [notes, setNotes] = useState(anomaly.investigator_notes || '')
  const [status, setStatus] = useState(anomaly.status)
  const [saving, setSaving] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiExplanation, setAiExplanation] = useState(null)

  const save = async () => {
    setSaving(true)
    try {
      await api.patch(`/anomalies/${anomaly.id}`, { status, investigator_notes: notes })
      onUpdate(anomaly.id, { status, investigator_notes: notes })
      setEditing(false)
    } catch(e) { alert('Save failed') }
    finally { setSaving(false) }
  }

  const getAiExplanation = async () => {
    setAiLoading(true)
    try {
      const res = await api.post(`/anomalies/${anomaly.id}/explain`)
      setAiExplanation(res.data)
    } catch (e) {
      alert('AI Explanation failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <div style={{ border:'1px solid var(--border)', borderRadius:'var(--radius)', marginBottom:12, overflow:'hidden', background:'var(--card-bg)' }}>
      <div style={{ padding:'14px 18px', display:'flex', alignItems:'flex-start', gap:14 }}>
        <div style={{ flexShrink:0, marginTop:2 }}>
          <span className={`badge ${SEV_MAP[anomaly.severity] || 'badge-grey'}`}>{anomaly.severity}</span>
        </div>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6, flexWrap:'wrap' }}>
            <span style={{ fontWeight:700, fontSize:12, color:'#38BDF8', fontFamily:'JetBrains Mono, monospace' }}>{anomaly.anomaly_id_str}</span>
            <span className={`badge badge-${anomaly.category === 'visual' ? 'blue' : anomaly.category === 'contextual' ? 'orange' : 'navy'}`}>
              {anomaly.category?.replace('_',' ')}
            </span>
            <span className={`badge ${status === 'false_positive' ? 'badge-green' : status === 'verified_observation' ? 'badge-navy' : status === 'requires_investigation' ? 'badge-red' : 'badge-grey'}`}>
              {STATUS_LABELS[status] || status}
            </span>
          </div>
          <p style={{ fontSize:13.5, color:'#F1F5F9', marginBottom:8, lineHeight:1.55, fontWeight:500 }}>{anomaly.description}</p>
          <div style={{ display:'flex', gap:16, fontSize:12, color:'#9CAFC4', flexWrap:'wrap' }}>
            <span><strong style={{ color:'#F1F5F9' }}>Doc:</strong> {anomaly.document_name}</span>
            <span><strong style={{ color:'#F1F5F9' }}>Confidence:</strong> {Math.round((anomaly.confidence || 0)*100)}%</span>
            <span><strong style={{ color:'#F1F5F9' }}>Method:</strong> {anomaly.detection_method}</span>
            {anomaly.page_number > 0 && <span><strong style={{ color:'#F1F5F9' }}>Page:</strong> {anomaly.page_number}</span>}
          </div>
          {anomaly.evidence_reference && (
            <div style={{ fontSize:12, color:'#38BDF8', marginTop:8, background:'rgba(19, 184, 213, 0.08)', border:'1px solid rgba(19, 184, 213, 0.25)', padding:'6px 12px', borderRadius:4, fontFamily:'JetBrains Mono, monospace' }}>
              <strong>Evidence Reference:</strong> {anomaly.evidence_reference}
            </div>
          )}
          {aiExplanation && (
            <div style={{ marginTop:10, padding:'12px 14px', background:'rgba(19, 184, 213, 0.06)', border:'1px solid rgba(19, 184, 213, 0.25)', borderRadius:6, fontSize:13, color:'#F1F5F9', lineHeight:1.55 }}>
              <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:4, color:'#13B8D5', fontWeight:700, fontSize:11, textTransform:'uppercase', letterSpacing:0.5 }}>
                <span>AI Forensic Reasoning ({aiExplanation.llm_status?.model || 'gpt-4o-mini'})</span>
              </div>
              {aiExplanation.explanation}
            </div>
          )}
          {anomaly.investigator_notes && !editing && (
            <div style={{ marginTop:8, padding:'8px 12px', background:'var(--bg-primary)', borderRadius:4, fontSize:12, color:'#F1F5F9', borderLeft:'3px solid #13B8D5' }}>
              <strong>Investigator Note:</strong> {anomaly.investigator_notes}
            </div>
          )}
        </div>
        <div style={{ display:'flex', gap:6, flexShrink:0 }}>
          <button className="btn btn-secondary btn-sm" onClick={getAiExplanation} disabled={aiLoading} title="Explain with AI">
            {aiLoading ? <span className="spinner" style={{ width:12, height:12 }} /> : 'AI Explain'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() => setEditing(e => !e)} title="Edit status & notes"><Edit3 size={13} /></button>
        </div>
      </div>
      {editing && (
        <div style={{ padding:'14px 18px', background:'var(--bg-secondary)', borderTop:'1px solid var(--border)' }}>
          <div style={{ display:'flex', gap:10, alignItems:'flex-end', flexWrap:'wrap' }}>
            <div style={{ flex:1, minWidth:200 }}>
              <label className="form-label" style={{ fontSize:11 }}>Update Status</label>
              <select className="form-control" value={status} onChange={e => setStatus(e.target.value)} style={{ fontSize:12, padding:'6px 10px' }}>
                {Object.entries(STATUS_LABELS).map(([v,l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div style={{ flex:2, minWidth:240 }}>
              <label className="form-label" style={{ fontSize:11 }}>Investigator Notes</label>
              <input className="form-control" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Add investigation notes..." style={{ fontSize:12, padding:'6px 12px' }} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
            <button className="btn btn-secondary btn-sm" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AnomalyAnalysis() {
  const { investigationId } = useParams()
  const [investigations, setInvestigations] = useState([])
  const [selectedInv, setSelectedInv] = useState(investigationId || '')
  const [anomalies, setAnomalies] = useState([])
  const [comparisons, setComparisons] = useState([])
  const [stats, setStats] = useState(null)
  const [filters, setFilters] = useState({ category: '', severity: '', status: '' })
  const [comparisonFilter, setComparisonFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [comparisonsLoading, setComparisonsLoading] = useState(false)
  const [comparisonError, setComparisonError] = useState('')
  const [reportGenerating, setReportGenerating] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/investigations/').then(r => {
      setInvestigations(r.data)
      if (!selectedInv && r.data[0]) setSelectedInv(String(r.data[0].id))
    })
  }, [])

  useEffect(() => {
    if (investigationId) setSelectedInv(investigationId)
  }, [investigationId])

  useEffect(() => {
    if (!selectedInv) return
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.category) params.set('category', filters.category)
    if (filters.severity) params.set('severity', filters.severity)
    Promise.all([
      api.get(`/anomalies/${selectedInv}?${params}`),
      api.get(`/anomalies/stats/${selectedInv}`)
    ]).then(([aRes, sRes]) => {
      let a = aRes.data
      if (filters.status) a = a.filter(x => x.status === filters.status)
      setAnomalies(a)
      setStats(sRes.data)
    }).catch(console.error).finally(() => setLoading(false))
  }, [selectedInv, filters])

  useEffect(() => {
    if (!selectedInv) {
      setComparisons([])
      return
    }

    let active = true
    setComparisonsLoading(true)
    setComparisonError('')
    api.get(`/analysis/correlate/${selectedInv}/results`)
      .then(response => {
        if (active) setComparisons(response.data)
      })
      .catch(error => {
        if (active) setComparisonError(error.response?.data?.detail || 'Could not load cross-document comparisons.')
      })
      .finally(() => {
        if (active) setComparisonsLoading(false)
      })

    return () => { active = false }
  }, [selectedInv])

  const onUpdate = (id, updates) => setAnomalies(prev => prev.map(a => a.id === id ? { ...a, ...updates } : a))

  const correlate = async () => {
    if (!selectedInv) return
    try {
      const r = await api.post(`/analysis/correlate/${selectedInv}`)
      setComparisons(r.data.matches.map(match => ({
        ...match,
        match_status: match.status,
      })))
      await generateAndDownloadDossier(selectedInv)
      alert(`Analysis complete: ${r.data.mismatches} mismatches found. The investigation report was generated and downloaded.`)
      setFilters(f => ({ ...f }))
    } catch(e) { alert('Error: ' + (e.response?.data?.detail || e.message)) }
  }

  const generateReport = async () => {
    if (!selectedInv) return
    setReportGenerating(true)
    try {
      await generateAndDownloadDossier(selectedInv)
    } catch(e) {
      alert('Report generation failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setReportGenerating(false)
    }
  }

  const visibleComparisons = comparisons.filter(match => (
    comparisonFilter === 'all' || match.match_status === comparisonFilter
  ))
  const mismatchCount = comparisons.filter(match => match.match_status === 'mismatch').length
  const partialCount = comparisons.filter(match => match.match_status === 'partial_match').length
  const matchCount = comparisons.filter(match => match.match_status === 'match').length

  return (
    <div className="fade-in">
      <div className="page-header">
        <div><h2>Anomaly Analysis</h2><p>Review and investigate detected forensic findings</p></div>
        <div style={{ display:'flex', gap:8 }}>
          {selectedInv && <button className="btn btn-secondary btn-sm" onClick={correlate}>Run Cross-Doc Correlation</button>}
          {selectedInv && <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/journal/${selectedInv}`)}>
            <NotebookPen size={14} /> Investigation Journal
          </button>}
          {selectedInv && <button className="btn btn-primary btn-sm" onClick={generateReport} disabled={reportGenerating}>
            <FileText size={14} /> {reportGenerating ? 'Generating Report…' : 'Generate & Download Report'}
          </button>}
          {selectedInv && <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/evidence`)}>Evidence Explorer</button>}
        </div>
      </div>

      {/* Investigation selector */}
      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-body" style={{ padding:'14px 20px' }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, flexWrap:'wrap' }}>
            <div style={{ flex:1, minWidth:200 }}>
              <label className="form-label" style={{ fontSize:11 }}>Investigation</label>
              <select className="form-control" value={selectedInv} onChange={e => setSelectedInv(e.target.value)} id="select-investigation">
                <option value="">Select Investigation…</option>
                {investigations.map(i => <option key={i.id} value={i.id}>INV-{String(i.id).padStart(4,'0')} — {i.name}</option>)}
              </select>
            </div>
            {stats && (
              <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
                {Object.entries(stats.by_severity).map(([sev, count]) => count > 0 && (
                  <div key={sev} style={{ textAlign:'center' }}>
                    <div style={{ fontSize:16, fontWeight:700, color: sev === 'Critical' ? '#DC2626' : sev === 'High' ? 'var(--danger)' : sev === 'Medium' ? 'var(--warning)' : '#13B8D5' }}>{count}</div>
                    <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase' }}>{sev}</div>
                  </div>
                ))}
                <div style={{ textAlign:'center' }}>
                  <div style={{ fontSize:16, fontWeight:700, color:'#F1F5F9' }}>{stats.total}</div>
                  <div style={{ fontSize:10, color:'#9CAFC4', textTransform:'uppercase', fontWeight:600 }}>Total</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-row">
        <Filter size={14} color="#13B8D5" />
        <select className="form-control" style={{ width:160, padding:'6px 10px', fontSize:12 }} value={filters.category} onChange={e => setFilters(f => ({ ...f, category: e.target.value }))}>
          <option value="">All Categories</option>
          <option value="visual">Visual</option>
          <option value="contextual">Contextual</option>
          <option value="cross_document">Cross-Document</option>
          <option value="structural">Structural</option>
        </select>
        <select className="form-control" style={{ width:140, padding:'6px 10px', fontSize:12 }} value={filters.severity} onChange={e => setFilters(f => ({ ...f, severity: e.target.value }))}>
          <option value="">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select className="form-control" style={{ width:180, padding:'6px 10px', fontSize:12 }} value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
          <option value="">All Statuses</option>
          <option value="detected">Detected</option>
          <option value="requires_investigation">Requires Investigation</option>
          <option value="verified_observation">Verified Observation</option>
          <option value="false_positive">False Positive</option>
        </select>
        <button className="btn btn-secondary btn-sm" onClick={() => setFilters({ category:'', severity:'', status:'' })}>Clear</button>
        <span style={{ fontSize:12, color:'#9CAFC4', marginLeft:'auto', fontWeight:600 }}>{anomalies.length} finding(s)</span>
      </div>

      <div className="alert alert-info" style={{ marginBottom:16 }}>
        <AlertTriangle size={14} style={{ flexShrink:0, marginTop:1 }} />
        All findings are automated observations requiring human verification. Use investigator actions to update the status of each finding.
      </div>

      <section className="card" style={{ marginBottom:20 }}>
        <div className="card-header" style={{ display:'flex', alignItems:'center', gap:12, flexWrap:'wrap' }}>
          <div style={{ flex:1 }}>
            <h3>Cross-Document Consistency Matrix</h3>
            <p style={{ fontSize:12, color:'#9CAFC4', marginTop:4 }}>
              Compare extracted field values across documents. Differences are review leads, not proof of fraud.
            </p>
          </div>
          <div style={{ display:'flex', gap:8, flexWrap:'wrap', alignItems:'center' }}>
            <span className="badge badge-red">{mismatchCount} mismatches</span>
            <span className="badge badge-orange">{partialCount} partial</span>
            <span className="badge badge-green">{matchCount} matches</span>
            <select
              className="form-control"
              aria-label="Filter cross-document comparisons"
              value={comparisonFilter}
              onChange={event => setComparisonFilter(event.target.value)}
              style={{ width:160, padding:'6px 10px', fontSize:12 }}
            >
              <option value="all">All comparisons</option>
              <option value="mismatch">Mismatches only</option>
              <option value="partial_match">Partial matches</option>
              <option value="match">Matches only</option>
            </select>
          </div>
        </div>
        {comparisonsLoading ? (
          <div className="loading-center" style={{ padding:24 }}><div className="spinner" /><span>Loading comparisons…</span></div>
        ) : comparisonError ? (
          <div className="alert alert-danger" style={{ margin:16 }}>{comparisonError}</div>
        ) : visibleComparisons.length === 0 ? (
          <div className="empty-state" style={{ padding:24 }}>
            <h4>{comparisons.length ? 'No comparisons match this filter' : 'No cross-document comparisons yet'}</h4>
            <p>{comparisons.length ? 'Choose another comparison filter.' : 'Run Cross-Doc Correlation after analyzing at least two documents to populate this matrix.'}</p>
          </div>
        ) : (
          <div style={{ overflowX:'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Field</th><th>Document 1</th><th>Extracted Value</th>
                  <th>Document 2</th><th>Extracted Value</th><th>Result</th><th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {visibleComparisons.map((match, index) => {
                  const status = match.match_status
                  const badgeClass = status === 'mismatch' ? 'badge-red' : status === 'partial_match' ? 'badge-orange' : 'badge-green'
                  return (
                    <tr key={match.id || `${match.field_name}-${match.doc1_id}-${match.doc2_id}-${index}`}>
                      <td style={{ fontWeight:700 }}>{match.field_name}</td>
                      <td>{match.doc1_name}</td>
                      <td style={{ maxWidth:220, overflowWrap:'anywhere' }}>{match.value1 || '—'}</td>
                      <td>{match.doc2_name}</td>
                      <td style={{ maxWidth:220, overflowWrap:'anywhere' }}>{match.value2 || '—'}</td>
                      <td><span className={`badge ${badgeClass}`}>{status.replace('_', ' ')}</span></td>
                      <td>{Math.round((match.confidence || 0) * 100)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {loading ? (
        <div className="loading-center"><div className="spinner" /><span>Loading anomalies…</span></div>
      ) : anomalies.length === 0 ? (
        <div className="empty-state">
          <CheckCircle size={36} />
          <h4>No anomalies found</h4>
          <p>{selectedInv ? 'No findings match your current filters, or processing is still in progress.' : 'Select an investigation to view its findings.'}</p>
        </div>
      ) : (
        <div>{anomalies.map(a => <AnomalyRow key={a.id} anomaly={a} onUpdate={onUpdate} />)}</div>
      )}
    </div>
  )
}
