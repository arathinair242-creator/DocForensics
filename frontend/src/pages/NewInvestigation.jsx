import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, X, FileText, File, CheckCircle, AlertTriangle, Loader } from 'lucide-react'
import api from '../services/api'
import { generateAndDownloadDossier } from '../services/dossier'

const DOC_TYPES = ['Identity Proof','Bank Statement','Salary Slip','Application Form',
  'Transaction Receipt','Invoice','Declaration','Supporting Document','Other']

function FileRow({ file, onRemove }) {
  const size = (file.size / 1024).toFixed(1)
  return (
    <div style={{ display:'flex', alignItems:'center', gap:10, padding:'10px 14px', background:'var(--bg-input)', borderRadius:'var(--radius)', marginTop:8, border:'1px solid var(--border-light)' }}>
      <FileText size={16} color="#C084FC" style={{ flexShrink:0 }} />
      <span style={{ flex:1, fontSize:13, fontWeight:600, color:'#FFFFFF', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{file.name}</span>
      <span style={{ fontSize:11, color:'#D8B4FE', whiteSpace:'nowrap' }}>{size} KB</span>
      <button className="btn-icon" onClick={onRemove} style={{ background:'none', border:'none', cursor:'pointer', color:'#D8B4FE', display:'flex', padding:4 }}><X size={14} /></button>
    </div>
  )
}

function UploadedDoc({ doc, onProcess }) {
  const [cls, setCls] = useState(doc.doc_type || 'Other')
  return (
    <div style={{ display:'flex', alignItems:'center', gap:10, padding:'12px 16px', border:'1px solid var(--border)', borderRadius:'var(--radius)', marginTop:8, background:'var(--bg-input)' }}>
      <span className={`status-dot ${doc.processing_status}`} />
      <span style={{ flex:1, fontSize:13, fontWeight:700, color:'#FFFFFF' }}>{doc.original_filename}</span>
      <select className="form-control" style={{ width:160, padding:'5px 8px', fontSize:12 }}
        value={cls} onChange={e => { setCls(e.target.value); api.patch(`/documents/${doc.id}/classification?doc_type=${encodeURIComponent(e.target.value)}`) }}>
        {DOC_TYPES.map(t => <option key={t}>{t}</option>)}
      </select>
      <span className={`badge badge-${doc.processing_status === 'completed' ? 'green' : doc.processing_status === 'processing' ? 'orange' : doc.processing_status === 'error' ? 'red' : 'grey'}`}>
        {doc.processing_status}
      </span>
      {doc.processing_status === 'pending' && (
        <button className="btn btn-blue btn-sm" onClick={() => onProcess(doc.id)}>Analyze</button>
      )}
    </div>
  )
}

export default function NewInvestigation() {
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [files, setFiles] = useState([])
  const [investigation, setInvestigation] = useState(null)
  const [uploadedDocs, setUploadedDocs] = useState([])
  const [uploading, setUploading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [processingAll, setProcessingAll] = useState(false)
  const navigate = useNavigate()

  const onDrop = useCallback(accepted => {
    const allowed = accepted.filter(f => /\.(pdf|jpg|jpeg|png)$/i.test(f.name))
    setFiles(prev => [...prev, ...allowed])
  }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg','.jpeg','.png'] } })

  const createInv = async () => {
    if (!name.trim()) return setError('Investigation name is required')
    if (files.length === 0) return setError('Add at least one document')
    setError(''); setCreating(true)
    try {
      const res = await api.post('/investigations/', { name: name.trim(), description: desc })
      const inv = res.data
      setInvestigation(inv)
      // Upload files sequentially
      setUploading(true)
      const docs = []
      for (const file of files) {
        const fd = new FormData()
        fd.append('investigation_id', inv.id)
        fd.append('file', file)
        try {
          const r = await api.post('/documents/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
          docs.push(r.data)
        } catch (e) { console.warn('Upload failed for:', file.name) }
      }
      setUploadedDocs(docs)
      setUploading(false)
    } catch (e) { setError(e.response?.data?.detail || 'Failed to create investigation') }
    finally { setCreating(false); setUploading(false) }
  }

  const processDoc = async (docId) => {
    try {
      await api.post(`/analysis/process/${docId}`)
      while (true) {
        await new Promise(resolve => window.setTimeout(resolve, 2000))
        const r = await api.get(`/analysis/status/${docId}`)
        setUploadedDocs(prev => prev.map(d => d.id === docId ? { ...d, processing_status: r.data.status, doc_type: r.data.doc_type } : d))
        if (r.data.status === 'completed' || r.data.status === 'error') return r.data.status
      }
    } catch (e) {
      setUploadedDocs(prev => prev.map(d => d.id === docId ? { ...d, processing_status: 'error' } : d))
      alert('Analysis failed: ' + (e.response?.data?.detail || e.message))
      return 'error'
    }
  }

  const processAll = async () => {
    setProcessingAll(true)
    try {
      const pending = uploadedDocs.filter(d => d.processing_status === 'pending')
      const results = []
      for (const doc of pending) results.push(await processDoc(doc.id))

      if (results.includes('error')) {
        alert('Some documents could not be analyzed. Review their status and retry before generating the report.')
        return
      }

      let analysis = { total: 0, mismatches: 0 }
      if (uploadedDocs.length >= 2) {
        const response = await api.post(`/analysis/correlate/${investigation.id}`)
        analysis = response.data
      }
      await generateAndDownloadDossier(investigation.id)
      alert(`Analysis complete: ${analysis.total || 0} comparisons, ${analysis.mismatches || 0} mismatches found. The report was generated and downloaded.`)
      navigate(`/anomalies/${investigation.id}`)
    } catch (e) {
      alert('Analysis or report generation failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setProcessingAll(false)
    }
  }

  const correlate = async () => {
    if (!investigation) return
    try {
      const r = await api.post(`/analysis/correlate/${investigation.id}`)
      await generateAndDownloadDossier(investigation.id)
      alert(`Cross-document analysis complete!\n${r.data.total || 0} comparisons, ${r.data.mismatches || 0} mismatches found.\nThe report was generated and downloaded.\n\nNavigating to Anomaly Analysis...`)
      navigate(`/anomalies/${investigation.id}`)
    } catch (e) { alert('Correlation error: ' + (e.response?.data?.detail || e.message)) }
  }

  const allComplete = uploadedDocs.length > 0 && uploadedDocs.every(d => d.processing_status === 'completed' || d.processing_status === 'error')

  return (
    <div className="fade-in" style={{ maxWidth: 740 }}>
      <div className="page-header">
        <div><h2>New Investigation</h2><p>Create an investigation and upload documents for analysis</p></div>
      </div>

      {!investigation ? (
        <div className="card">
          <div className="card-header"><h3>Investigation Details</h3></div>
          <div className="card-body">
            {error && <div className="alert alert-danger"><AlertTriangle size={14} />{error}</div>}
            <div className="form-group">
              <label className="form-label">Investigation Name <span style={{ color:'var(--danger)' }}>*</span></label>
              <input className="form-control" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Loan Application — Arun Kumar" id="inp-inv-name" />
            </div>
            <div className="form-group">
              <label className="form-label">Description (optional)</label>
              <textarea className="form-control" value={desc} onChange={e => setDesc(e.target.value)} rows={2} placeholder="Describe the nature of this investigation..." />
            </div>
            <div className="form-group">
              <label className="form-label">Documents</label>
              <div {...getRootProps()} className={`dropzone${isDragActive ? ' active' : ''}`} id="dropzone">
                <input {...getInputProps()} />
                <div className="dropzone-icon"><Upload size={28} /></div>
                <div className="dropzone-text">Drag &amp; drop files here, or click to browse</div>
                <div className="dropzone-hint">Supports PDF, JPG, JPEG, PNG — max 50MB each</div>
              </div>
              {files.map((f, i) => <FileRow key={i} file={f} onRemove={() => setFiles(prev => prev.filter((_, j) => j !== i))} />)}
            </div>
            <button className="btn btn-primary btn-lg" onClick={createInv} disabled={creating || uploading} id="btn-create-investigation">
              {creating ? <Loader size={15} className="spinner" /> : <Upload size={15} />}
              {creating ? 'Creating…' : 'Create Investigation & Upload'}
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div className="alert alert-success" style={{ marginBottom: 20 }}>
            <CheckCircle size={15} style={{ flexShrink:0 }} />
            <span>Investigation <strong>INV-{String(investigation.id).padStart(4,'0')}</strong> created. {uploading ? 'Uploading documents…' : `${uploadedDocs.length} document(s) uploaded.`}</span>
          </div>
          <div className="card">
            <div className="card-header">
              <h3>Uploaded Documents</h3>
              <div style={{ display:'flex', gap:8 }}>
                {!allComplete && <button className="btn btn-blue btn-sm" onClick={processAll} disabled={processingAll} id="btn-analyze-all">
                  {processingAll ? <Loader size={13} /> : null} {processingAll ? 'Analyzing…' : 'Analyze All & Generate Report'}
                </button>}
                {allComplete && uploadedDocs.length >= 2 && (
                  <button className="btn btn-primary btn-sm" onClick={correlate} id="btn-correlate">
                    Run Cross-Document Correlation
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              {uploading && <div style={{ display:'flex', gap:8, alignItems:'center', color:'var(--text-med)', marginBottom:12 }}><div className="spinner" /><span>Uploading files…</span></div>}
              {uploadedDocs.map(doc => <UploadedDoc key={doc.id} doc={doc} onProcess={processDoc} />)}
            </div>
          </div>
          {allComplete && (
            <div style={{ marginTop:16, display:'flex', gap:10 }}>
              <button className="btn btn-primary" onClick={() => navigate(`/anomalies/${investigation.id}`)}>View Anomaly Analysis</button>
              <button className="btn btn-secondary" onClick={() => navigate('/')}>Back to Dashboard</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
