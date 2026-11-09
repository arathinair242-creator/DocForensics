import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { NotebookPen, Send } from 'lucide-react'
import api from '../services/api'

const EMPTY_DRAFT = { note_type: 'lead', title: '', content: '', anomaly_id: '' }

export default function InvestigationJournal() {
  const { investigationId } = useParams()
  const [investigations, setInvestigations] = useState([])
  const [selectedInv, setSelectedInv] = useState(investigationId || '')
  const [anomalies, setAnomalies] = useState([])
  const [entries, setEntries] = useState([])
  const [draft, setDraft] = useState(EMPTY_DRAFT)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api.get('/investigations/').then(response => {
      if (!active) return
      setInvestigations(response.data)
      if (!investigationId && response.data[0]) setSelectedInv(String(response.data[0].id))
    }).catch(requestError => {
      if (active) setError(requestError.response?.data?.detail || 'Could not load investigations.')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [investigationId])

  useEffect(() => {
    if (investigationId) setSelectedInv(investigationId)
  }, [investigationId])

  useEffect(() => {
    if (!selectedInv) {
      setEntries([])
      setAnomalies([])
      return
    }

    let active = true
    setLoading(true)
    setError('')
    Promise.all([
      api.get(`/investigations/${selectedInv}/notes`),
      api.get(`/anomalies/${selectedInv}`),
    ]).then(([notesResponse, anomaliesResponse]) => {
      if (!active) return
      setEntries(notesResponse.data)
      setAnomalies(anomaliesResponse.data)
    }).catch(requestError => {
      if (active) setError(requestError.response?.data?.detail || 'Could not load journal entries.')
    }).finally(() => {
      if (active) setLoading(false)
    })

    return () => { active = false }
  }, [selectedInv])

  const saveEntry = async event => {
    event.preventDefault()
    if (!selectedInv) return

    setSaving(true)
    setError('')
    try {
      const response = await api.post(`/investigations/${selectedInv}/notes`, {
        ...draft,
        anomaly_id: draft.anomaly_id ? Number(draft.anomaly_id) : null,
      })
      setEntries(current => [response.data, ...current])
      setDraft(EMPTY_DRAFT)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not save this journal entry.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>Investigation Journal</h2>
          <p>Document leads, follow-ups, findings, and conclusions for a case.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-body">
          <label className="form-label" htmlFor="journal-investigation">Investigation</label>
          <select
            id="journal-investigation"
            className="form-control"
            value={selectedInv}
            onChange={event => setSelectedInv(event.target.value)}
          >
            <option value="">Select Investigation…</option>
            {investigations.map(investigation => (
              <option key={investigation.id} value={investigation.id}>
                INV-{String(investigation.id).padStart(4, '0')} — {investigation.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!selectedInv ? (
        <div className="empty-state">
          <NotebookPen size={36} />
          <h4>{loading ? 'Loading investigations…' : 'Select an investigation'}</h4>
          <p>Choose a case to view and add its journal entries.</p>
        </div>
      ) : (
        <>
          <section className="card" style={{ marginBottom:20 }}>
            <div className="card-header">
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <NotebookPen size={18} color="#13B8D5" />
                <div>
                  <h3>New Journal Entry</h3>
                  <p style={{ fontSize:12, color:'#9CAFC4', marginTop:4 }}>
                    Keep investigator observations and next steps separate from automated findings.
                  </p>
                </div>
              </div>
            </div>
            <form onSubmit={saveEntry} className="card-body">
              {error && <div className="alert alert-danger" style={{ marginBottom:12 }}>{error}</div>}
              <div style={{ display:'grid', gridTemplateColumns:'minmax(150px, 0.7fr) minmax(200px, 1fr)', gap:12 }}>
                <div>
                  <label className="form-label" htmlFor="journal-type">Entry type</label>
                  <select id="journal-type" className="form-control" value={draft.note_type}
                    onChange={event => setDraft(current => ({ ...current, note_type:event.target.value }))}>
                    <option value="lead">Lead</option>
                    <option value="follow_up">Follow-up</option>
                    <option value="finding">Investigator finding</option>
                    <option value="conclusion">Conclusion</option>
                  </select>
                </div>
                <div>
                  <label className="form-label" htmlFor="journal-title">Title</label>
                  <input id="journal-title" className="form-control" maxLength={120} required
                    value={draft.title}
                    onChange={event => setDraft(current => ({ ...current, title:event.target.value }))}
                    placeholder="e.g. Verify employer details with applicant" />
                </div>
              </div>
              <div style={{ marginTop:12 }}>
                <label className="form-label" htmlFor="journal-content">Investigator notes</label>
                <textarea id="journal-content" className="form-control" required maxLength={5000} rows={3}
                  value={draft.content}
                  onChange={event => setDraft(current => ({ ...current, content:event.target.value }))}
                  placeholder="Record what you observed, what needs checking, and the next step…" />
              </div>
              <div style={{ display:'flex', alignItems:'flex-end', gap:10, marginTop:12, flexWrap:'wrap' }}>
                <div style={{ flex:1, minWidth:220 }}>
                  <label className="form-label" htmlFor="journal-anomaly">Link to a finding (optional)</label>
                  <select id="journal-anomaly" className="form-control" value={draft.anomaly_id}
                    onChange={event => setDraft(current => ({ ...current, anomaly_id:event.target.value }))}>
                    <option value="">No linked finding</option>
                    {anomalies.map(anomaly => (
                      <option key={anomaly.id} value={anomaly.id}>
                        {anomaly.anomaly_id_str} · {anomaly.description.slice(0, 90)}
                      </option>
                    ))}
                  </select>
                </div>
                <button type="submit" className="btn btn-primary" disabled={saving || !selectedInv}>
                  <Send size={14} /> {saving ? 'Saving…' : 'Add Journal Entry'}
                </button>
              </div>
            </form>
          </section>

          <section className="card">
            <div className="card-header">
              <h3>Case Notes ({entries.length})</h3>
            </div>
            {loading ? (
              <div className="loading-center" style={{ padding:20 }}><div className="spinner" /><span>Loading journal…</span></div>
            ) : entries.length === 0 ? (
              <div className="empty-state" style={{ padding:24 }}>
                <p>No journal entries yet. Add a lead or follow-up to document this investigation.</p>
              </div>
            ) : entries.map(entry => (
              <article key={entry.id} style={{ padding:'14px 20px', borderBottom:'1px solid var(--border)' }}>
                <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
                  <span className="badge badge-navy">{entry.note_type.replace('_', ' ')}</span>
                  <strong style={{ color:'#F1F5F9', fontSize:13 }}>{entry.title}</strong>
                  {entry.anomaly_id && <span className="badge badge-orange">Linked finding #{entry.anomaly_id}</span>}
                </div>
                <p style={{ marginTop:8, fontSize:13, color:'#D8B4FE', whiteSpace:'pre-wrap', overflowWrap:'anywhere' }}>{entry.content}</p>
                <div style={{ marginTop:8, fontSize:11, color:'#9CAFC4' }}>
                  {entry.author} · {new Date(entry.created_at).toLocaleString()}
                </div>
              </article>
            ))}
          </section>
        </>
      )}
    </div>
  )
}
