import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Eye, Loader, RefreshCw } from 'lucide-react'
import api from '../services/api'

export default function Documents() {
  const [investigations, setInvestigations] = useState([])
  const [selectedInv, setSelectedInv] = useState('')
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/investigations/').then(r => {
      setInvestigations(r.data)
      if (r.data[0]) setSelectedInv(String(r.data[0].id))
    })
  }, [])

  useEffect(() => {
    if (!selectedInv) return
    setLoading(true)
    api.get(`/documents/by-investigation/${selectedInv}`).then(r => setDocs(r.data)).finally(() => setLoading(false))
  }, [selectedInv])

  const processDoc = async (docId) => {
    setProcessing(p => ({ ...p, [docId]: true }))
    try {
      await api.post(`/analysis/process/${docId}`)
      const poll = setInterval(async () => {
        const r = await api.get(`/analysis/status/${docId}`)
        setDocs(prev => prev.map(d => d.id === docId ? { ...d, processing_status: r.data.status, doc_type: r.data.doc_type, classification_confidence: r.data.confidence } : d))
        if (r.data.status === 'completed' || r.data.status === 'error') {
          clearInterval(poll)
          setProcessing(p => ({ ...p, [docId]: false }))
        }
      }, 2000)
    } catch(e) {
      alert('Processing error: ' + (e.response?.data?.detail || e.message))
      setProcessing(p => ({ ...p, [docId]: false }))
    }
  }

  const viewDoc = (docId) => navigate(`/evidence/${docId}`)

  return (
    <div className="fade-in">
      <div className="page-header">
        <div><h2>Documents</h2><p>Manage and analyze submitted documents</p></div>
      </div>
      <div className="card" style={{ marginBottom:16, padding:'12px 16px' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <label className="form-label" style={{ fontSize:11, whiteSpace:'nowrap', margin:0 }}>Investigation</label>
          <select className="form-control" value={selectedInv} onChange={e => setSelectedInv(e.target.value)} id="select-inv-docs">
            <option value="">Select Investigation…</option>
            {investigations.map(i => <option key={i.id} value={i.id}>INV-{String(i.id).padStart(4,'0')} — {i.name}</option>)}
          </select>
          <button className="btn btn-secondary btn-sm" onClick={() => { if (selectedInv) { setLoading(true); api.get(`/documents/by-investigation/${selectedInv}`).then(r => setDocs(r.data)).finally(() => setLoading(false)) } }}><RefreshCw size={13} /></button>
        </div>
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner spinner-lg" /></div>
      ) : docs.length === 0 ? (
        <div className="empty-state"><FileText size={40} /><h4>No documents found</h4><p>Upload documents via New Investigation.</p></div>
      ) : (
        <div className="card">
          <table className="data-table">
            <thead><tr>
              <th>Document</th><th>Type</th><th>Confidence</th><th>Pages</th><th>Size</th><th>Status</th><th>Actions</th>
            </tr></thead>
            <tbody>
              {docs.map(doc => (
                <tr key={doc.id}>
                  <td>
                    <div style={{ fontWeight:700, fontSize:13, color:'#FFFFFF' }}>{doc.original_filename}</div>
                    <div style={{ fontSize:11, color:'#D8B4FE' }}>ID: DOC-{String(doc.id).padStart(4,'0')}</div>
                  </td>
                  <td><span className="badge badge-navy" style={{ fontSize:10 }}>{doc.doc_type || 'Unclassified'}</span></td>
                  <td>{doc.classification_confidence ? `${Math.round(doc.classification_confidence*100)}%` : '—'}</td>
                  <td>{doc.page_count || '—'}</td>
                  <td>{doc.file_size ? `${(doc.file_size/1024).toFixed(1)} KB` : '—'}</td>
                  <td>
                    <span className={`badge badge-${doc.processing_status === 'completed' ? 'green' : doc.processing_status === 'processing' ? 'orange' : doc.processing_status === 'error' ? 'red' : 'grey'}`}>
                      {doc.processing_status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display:'flex', gap:6 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => viewDoc(doc.id)}><Eye size={12} /> View</button>
                      {(doc.processing_status === 'pending' || doc.processing_status === 'error') && (
                        <button className="btn btn-blue btn-sm" onClick={() => processDoc(doc.id)} disabled={processing[doc.id]}>
                          {processing[doc.id] ? <Loader size={12} /> : <RefreshCw size={12} />} Analyze
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
