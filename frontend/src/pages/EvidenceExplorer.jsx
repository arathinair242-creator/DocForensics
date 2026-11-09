import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { ZoomIn, ZoomOut, Eye, AlertTriangle } from 'lucide-react'
import api from '../services/api'

const SEV_COLORS = { Critical: '#DC2626', High: '#EF4444', Medium: '#F59E0B', Low: '#13B8D5' }

export default function EvidenceExplorer() {
  const { documentId: paramDocId } = useParams()
  const [investigations, setInvestigations] = useState([])
  const [selectedInv, setSelectedInv] = useState('')
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(paramDocId || '')
  const [docData, setDocData] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [zoom, setZoom] = useState(100)
  const [previewUrl, setPreviewUrl] = useState('')
  const [previewMimeType, setPreviewMimeType] = useState('')
  const [previewError, setPreviewError] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [useAnnotated, setUseAnnotated] = useState(false)

  useEffect(() => {
    api.get('/investigations/').then(r => { setInvestigations(r.data); if (r.data[0]) setSelectedInv(String(r.data[0].id)) })
  }, [])

  useEffect(() => {
    if (!selectedInv) return
    api.get(`/documents/by-investigation/${selectedInv}`).then(r => setDocuments(r.data))
    api.get(`/anomalies/${selectedInv}`).then(r => setAnomalies(r.data))
  }, [selectedInv])

  useEffect(() => {
    if (!selectedDoc) return
    setDocData(null)
    api.get(`/documents/${selectedDoc}`).then(r => setDocData(r.data))
  }, [selectedDoc])

  useEffect(() => {
    if (!selectedDoc) {
      setPreviewUrl('')
      return
    }

    let active = true
    let objectUrl = ''
    setPreviewUrl('')
    setPreviewMimeType('')
    setPreviewError(false)
    setPreviewLoading(true)

    api.get(`/documents/${selectedDoc}/${useAnnotated ? 'annotated' : 'preview'}`, {
      responseType: 'blob',
    }).then(response => {
      objectUrl = URL.createObjectURL(response.data)
      if (active) {
        setPreviewUrl(objectUrl)
        setPreviewMimeType(response.data.type || response.headers['content-type'] || '')
      } else {
        URL.revokeObjectURL(objectUrl)
      }
    }).catch(() => {
      if (active) setPreviewError(true)
    }).finally(() => {
      if (active) setPreviewLoading(false)
    })

    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [selectedDoc, useAnnotated])

  const isPdf = previewMimeType === 'application/pdf' || (
    !useAnnotated && /\.pdf$/i.test(docData?.original_filename || '')
  )

  const docAnomalies = anomalies.filter(a => String(a.document_id) === String(selectedDoc))

  return (
    <div className="fade-in">
      <div className="page-header">
        <div><h2>Evidence Explorer</h2><p>Inspect document evidence and highlighted anomaly regions</p></div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'240px 1fr 280px', gap:16, height:'calc(100vh - 180px)', minHeight:500 }}>
        {/* Left panel - selectors */}
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          <div className="card" style={{ padding:14 }}>
            <label className="form-label" style={{ fontSize:11 }}>Investigation</label>
            <select className="form-control" value={selectedInv} onChange={e => setSelectedInv(e.target.value)} style={{ fontSize:12, padding:'5px 8px', marginTop:4 }}>
              {investigations.map(i => <option key={i.id} value={i.id}>INV-{String(i.id).padStart(4,'0')} — {i.name.slice(0,25)}</option>)}
            </select>
          </div>
          <div className="card" style={{ padding:14, flex:1, overflow:'auto' }}>
            <label className="form-label" style={{ fontSize:11 }}>Documents</label>
            <div style={{ marginTop:6, display:'flex', flexDirection:'column', gap:4 }}>
              {documents.map(d => (
                <button key={d.id} onClick={() => setSelectedDoc(String(d.id))}
                  style={{
                    textAlign:'left',
                    padding:'8px 10px',
                    borderRadius:'var(--radius)',
                    fontSize:12,
                    cursor:'pointer',
                    border:`1px solid ${String(selectedDoc) === String(d.id) ? '#13B8D5' : 'var(--border)'}`,
                    background: String(selectedDoc) === String(d.id) ? 'rgba(19, 184, 213, 0.12)' : 'var(--bg-primary)',
                    display:'flex',
                    flexDirection:'column',
                    gap:2
                  }}>
                  <span style={{ fontWeight:600, color:'#F1F5F9' }}>{d.original_filename.slice(0,26)}</span>
                  <span style={{ fontSize:10, color:'#9CAFC4' }}>{d.doc_type} · {d.processing_status}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Center - document viewer */}
        <div className="card" style={{ display:'flex', flexDirection:'column', overflow:'hidden' }}>
          <div style={{ padding:'10px 14px', borderBottom:'1px solid var(--border)', display:'flex', alignItems:'center', gap:8, background:'var(--bg-secondary)' }}>
            <span style={{ fontWeight:600, fontSize:13, color:'#F1F5F9' }}>{docData?.original_filename || 'Select a document'}</span>
            {docData && <span className="badge badge-navy">{docData.doc_type}</span>}
            <div style={{ marginLeft:'auto', display:'flex', gap:6 }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setZoom(z => Math.max(50, z-25))}><ZoomOut size={13} /></button>
              <span style={{ fontSize:12, minWidth:40, textAlign:'center', lineHeight:'26px', color:'#F1F5F9', fontWeight:600 }}>{zoom}%</span>
              <button className="btn btn-secondary btn-sm" onClick={() => setZoom(z => Math.min(200, z+25))}><ZoomIn size={13} /></button>
              {docData?.annotated_path && (
                <button className={`btn btn-sm ${useAnnotated ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setUseAnnotated(u => !u)}>
                  <Eye size={12} /> {useAnnotated ? 'Annotated' : 'Original'}
                </button>
              )}
            </div>
          </div>
          <div style={{ flex:1, overflow:'auto', background:'var(--bg-primary)', display:'flex', alignItems:'flex-start', justifyContent:'center', padding:20 }}>
            {previewLoading ? (
              <div style={{ color:'#9CAFC4', textAlign:'center' }}>Loading document preview…</div>
            ) : previewError ? (
              <div style={{ color:'var(--text-muted)', textAlign:'center', padding:40 }}>
                <AlertTriangle size={30} style={{ marginBottom:12, color:'#F59E0B' }} />
                <div style={{ color:'#F1F5F9', fontWeight:600 }}>Document preview could not be loaded.</div>
                <div style={{ fontSize:12, marginTop:6, color:'#9CAFC4' }}>Check that the backend is running, then select the document again.</div>
              </div>
            ) : previewUrl && isPdf ? (
              <iframe
                src={previewUrl}
                title={`PDF preview: ${docData?.original_filename || 'document'}`}
                style={{ width:`${zoom}%`, height:`${zoom}%`, minHeight:'100%', border:0, background:'#fff' }}
              />
            ) : previewUrl ? (
              <img src={previewUrl} alt="Document" onError={() => setPreviewError(true)}
                style={{ width:`${zoom}%`, maxWidth:'none', borderRadius:4, boxShadow:'0 4px 20px rgba(0,0,0,0.6)' }} />
            ) : selectedDoc ? (
              <div style={{ color:'#9CAFC4', textAlign:'center' }}>Preparing document preview…</div>
            ) : (
              <div style={{ color:'var(--text-muted)', textAlign:'center' }}>
                <Eye size={36} style={{ marginBottom:12, color:'#64748B' }} />
                <div style={{ color:'#9CAFC4' }}>Select a document to preview</div>
              </div>
            )}
          </div>
        </div>

        {/* Right panel - anomalies + extracted fields */}
        <div style={{ display:'flex', flexDirection:'column', gap:12, overflow:'auto' }}>
          <div className="card" style={{ flex:'0 0 auto' }}>
            <div className="card-header" style={{ padding:'10px 14px' }}><h3 style={{ fontSize:13 }}>Document Anomalies ({docAnomalies.length})</h3></div>
            <div style={{ maxHeight:280, overflowY:'auto' }}>
              {docAnomalies.length === 0 ? (
                <div style={{ padding:'16px', fontSize:12, color:'var(--text-muted)', textAlign:'center' }}>No anomalies for this document</div>
              ) : docAnomalies.map(a => (
                <div key={a.id} onClick={() => setSelectedAnomaly(a.id === selectedAnomaly ? null : a.id)}
                  style={{ padding:'10px 14px', borderBottom:'1px solid var(--border)', cursor:'pointer', background: selectedAnomaly === a.id ? 'rgba(19, 184, 213, 0.12)' : 'transparent', transition:'background 0.15s' }}>
                  <div style={{ display:'flex', gap:6, alignItems:'center', marginBottom:4 }}>
                    <span style={{ fontSize:11, fontFamily:'JetBrains Mono, monospace', fontWeight:700, color:'#38BDF8' }}>{a.anomaly_id_str}</span>
                    <span className="badge" style={{ fontSize:9, padding:'1px 6px', background: SEV_COLORS[a.severity]+'22', color: SEV_COLORS[a.severity] }}>{a.severity}</span>
                  </div>
                  <div style={{ fontSize:12, color:'#F1F5F9', lineHeight:1.45 }}>{a.description.slice(0,100)}…</div>
                  <div style={{ fontSize:10, color:'#13B8D5', marginTop:3 }}>{a.detection_method}</div>
                </div>
              ))}
            </div>
          </div>

          {docData?.extracted_fields?.length > 0 && (
            <div className="card" style={{ flex:1, overflow:'hidden', display:'flex', flexDirection:'column' }}>
              <div className="card-header" style={{ padding:'10px 14px' }}>
                <h3 style={{ fontSize:13 }}>Extracted Fields ({docData.extracted_fields.length})</h3>
              </div>
              <div style={{ flex:1, overflowY:'auto' }}>
                {docData.extracted_fields.map(f => (
                  <div key={f.id} style={{ padding:'8px 14px', borderBottom:'1px solid var(--border)' }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:1 }}>
                      <span style={{ fontSize:11, fontWeight:600, color:'#F1F5F9' }}>{f.field_name}</span>
                      <span style={{ fontSize:10, color:'#13B8D5', fontWeight:700 }}>{Math.round(f.confidence*100)}%</span>
                    </div>
                    <div style={{ fontSize:12, color:'#F1F5F9' }}>{f.field_value}</div>
                    <div style={{ fontSize:10, color:'#9CAFC4' }}>{f.section} · Page {f.page_number}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
