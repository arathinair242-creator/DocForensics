import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewInvestigation from './pages/NewInvestigation'
import Documents from './pages/Documents'
import InvestigationHistory from './pages/InvestigationHistory'
import AnomalyAnalysis from './pages/AnomalyAnalysis'
import InvestigationJournal from './pages/InvestigationJournal'
import EvidenceExplorer from './pages/EvidenceExplorer'
import Dossiers from './pages/Dossiers'
import AuditTrail from './pages/AuditTrail'
import Settings from './pages/Settings'

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return children
}

function PublicRoute({ children }) {
  const { user } = useAuth()
  if (user) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="new-investigation" element={<NewInvestigation />} />
            <Route path="documents" element={<Documents />} />
            <Route path="history" element={<InvestigationHistory />} />
            <Route path="anomalies" element={<AnomalyAnalysis />} />
            <Route path="anomalies/:investigationId" element={<AnomalyAnalysis />} />
            <Route path="journal" element={<InvestigationJournal />} />
            <Route path="journal/:investigationId" element={<InvestigationJournal />} />
            <Route path="evidence" element={<EvidenceExplorer />} />
            <Route path="evidence/:documentId" element={<EvidenceExplorer />} />
            <Route path="dossiers" element={<Dossiers />} />
            <Route path="audit" element={<AuditTrail />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
