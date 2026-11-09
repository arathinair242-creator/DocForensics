import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, AlertTriangle, CheckCircle, BarChart2, Clock, Plus, FlaskConical } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../services/api'

const SEV_COLORS = { Critical: '#DC2626', High: '#EF4444', Medium: '#F59E0B', Low: '#13B8D5' }

function StatCard({ icon: Icon, label, value, colorClass }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${colorClass}`}><Icon size={18} /></div>
      <div>
        <div className="stat-value">{value ?? '—'}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

function timeAgo(ts) {
  if (!ts) return ''
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [demoLoading, setDemoLoading] = useState(false)
  const navigate = useNavigate()

  const load = async () => {
    try {
      const res = await api.get('/investigations/dashboard-stats')
      setStats(res.data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t) }, [])

  const loadDemo = async () => {
    setDemoLoading(true)
    try {
      const res = await api.post('/demo/load')
      alert(`Demo investigation created! Investigation ID: ${res.data.investigation_id}. Documents are being processed — check Investigation History in ~30 seconds.`)
      load()
      navigate(`/anomalies/${res.data.investigation_id}`)
    } catch (e) {
      alert('Failed to load demo: ' + (e.response?.data?.detail || e.message))
    } finally { setDemoLoading(false) }
  }

  const chartData = stats ? [
    { name: 'Investigations', value: stats.total_investigations },
    { name: 'Documents', value: stats.total_documents },
    { name: 'Anomalies', value: stats.total_anomalies },
    { name: 'Critical', value: stats.critical_anomalies },
    { name: 'Pending', value: stats.pending_documents },
  ] : []

  if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /><span>Loading dashboard metrics...</span></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>Investigation Overview</h2>
          <p>Real-time platform metrics and live anomaly telemetry</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={loadDemo} disabled={demoLoading} id="btn-load-demo">
            <FlaskConical size={14} />
            {demoLoading ? 'Preparing…' : 'Load Demo Investigation'}
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/new-investigation')} id="btn-new-investigation">
            <Plus size={14} />
            New Investigation
          </button>
        </div>
      </div>

      <div className="alert alert-warning" style={{ marginBottom: 20 }}>
        <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
        <span><strong>Verification Protocol:</strong> Findings represent potential structural anomalies requiring human verification. No automated observation constitutes conclusive confirmation of fraud.</span>
      </div>

      <div className="stat-grid">
        <StatCard icon={BarChart2} label="Total Investigations" value={stats?.total_investigations} colorClass="navy" />
        <StatCard icon={FileText} label="Documents Processed" value={stats?.total_documents} colorClass="blue" />
        <StatCard icon={CheckCircle} label="Completed Documents" value={stats?.requiring_review} colorClass="green" />
        <StatCard icon={AlertTriangle} label="Anomalies Detected" value={stats?.total_anomalies} colorClass="orange" />
        <StatCard icon={AlertTriangle} label="Critical Findings" value={stats?.critical_anomalies} colorClass="red" />
        <StatCard icon={Clock} label="Pending Processing" value={stats?.pending_documents} colorClass="navy" />
      </div>

      <div className="two-col" style={{ marginBottom: 20 }}>
        {/* Chart */}
        <div className="card">
          <div className="card-header"><h3>Platform Telemetry</h3></div>
          <div className="card-body">
            {chartData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} margin={{ top: 0, right: 10, bottom: 0, left: -20 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CAFC4' }} stroke="#25364A" />
                  <YAxis tick={{ fontSize: 11, fill: '#9CAFC4' }} stroke="#25364A" allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 6,
                      background: '#111C2D',
                      border: '1px solid #25364A',
                      color: '#F1F5F9',
                      boxShadow: '0 4px 16px rgba(0,0,0,0.5)'
                    }}
                    itemStyle={{ color: '#13B8D5' }}
                  />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={['#13B8D5', '#38BDF8', '#F59E0B', '#DC2626', '#64748B'][i]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state" style={{ padding: '36px 20px' }}>
                <BarChart2 size={28} />
                <h4>No Telemetry Yet</h4>
                <p>Start an investigation to populate metrics here.</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="card-header"><h3>Recent Activity</h3></div>
          <div style={{ maxHeight: 250, overflowY: 'auto' }}>
            {stats?.recent_activities?.length ? (
              stats.recent_activities.map((log, i) => (
                <div key={i} style={{ padding: '10px 18px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13, color: '#F1F5F9' }}>{log.activity}</div>
                    <div style={{ fontSize: 12, color: '#9CAFC4', marginTop: 2 }}>{log.details?.slice(0, 60)}</div>
                  </div>
                  <span style={{ fontSize: 11, color: '#64748B', whiteSpace: 'nowrap', marginLeft: 12 }}>{timeAgo(log.timestamp)}</span>
                </div>
              ))
            ) : (
              <div className="empty-state" style={{ padding: '30px' }}>
                <Clock size={24} /><h4>No activity recorded</h4>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Investigations */}
      <div className="card">
        <div className="card-header">
          <h3>Recent Investigations</h3>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/history')}>View All</button>
        </div>
        {stats?.recent_investigations?.length ? (
          <table className="data-table">
            <thead><tr>
              <th>Investigation</th><th>Status</th><th>Started</th><th>Action</th>
            </tr></thead>
            <tbody>{stats.recent_investigations.map(inv => (
              <tr key={inv.id}>
                <td><span style={{ fontWeight: 600, fontFamily: 'monospace', color: '#38BDF8' }}>INV-{String(inv.id).padStart(4, '0')}</span> — {inv.name}</td>
                <td><span className={`badge badge-${inv.status === 'completed' ? 'green' : inv.status === 'in_progress' ? 'orange' : 'grey'}`}>{inv.status}</span></td>
                <td>{new Date(inv.created_at).toLocaleDateString()}</td>
                <td>
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/anomalies/${inv.id}`)}>View Findings</button>
                </td>
              </tr>
            ))}</tbody>
          </table>
        ) : (
          <div className="empty-state">
            <FileText size={32} /><h4>No investigations yet</h4>
            <p>Click "New Investigation" to get started, or use "Load Demo Investigation" to review sample forensic evidence.</p>
          </div>
        )}
      </div>
    </div>
  )
}
