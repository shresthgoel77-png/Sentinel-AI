import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';
import OverviewPage from './pages/OverviewPage';
import ComingSoonPage from './pages/ComingSoonPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ApplicationDetailPage from './pages/ApplicationDetailPage';
import IncidentsPage from './pages/IncidentsPage';
import IncidentDetailPage from './pages/IncidentDetailPage';
import AuditPage from './pages/AuditPage';
import PoliciesPage from './pages/PoliciesPage';
import TrafficPage from './pages/TrafficPage';
import SettingsPage from './pages/SettingsPage';
import TeamPage from './pages/TeamPage';
import LandingPage from './pages/LandingPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="incidents/:id" element={<IncidentDetailPage />} />
          <Route path="policies" element={<PoliciesPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="applications/:id" element={<ApplicationDetailPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="traffic" element={<TrafficPage />} />
          <Route path="team" element={<TeamPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}