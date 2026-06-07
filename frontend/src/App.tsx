import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './state/auth';
import { ActiveProfileProvider } from './state/activeProfile';
import { BottomNav } from './components/layout/BottomNav';
import { LoginScreen } from './features/auth/LoginScreen';
import { HomeDashboard } from './pages/HomeDashboard';
import { PurchaseAdvisor } from './pages/PurchaseAdvisor';
import { ComparisonResults } from './pages/ComparisonResults';
import { ProfilePage } from './pages/ProfilePage';
import { getDemoProfileId } from './api/endpoints';
import './pages/pages.css';

const DEMO_CIF = "10001234";

function AppShell() {
  const { token, logout } = useAuth();
  const [profileId, setProfileId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (token) {
      getDemoProfileId().then(r => setProfileId(r.id)).catch(console.error);
    }
  }, [token]);

  if (!token) return <LoginScreen />;

  if (!profileId) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  const handleProfileUpdated = () => setRefreshKey(k => k + 1);

  return (
    <BrowserRouter>
      <div className="app-content" style={{ paddingBottom: 'var(--nav-height)' }}>
        <Routes>
          <Route path="/" element={
            <HomeDashboard key={refreshKey} profileId={profileId} cif={DEMO_CIF} />
          } />
          <Route path="/advisor" element={
            <PurchaseAdvisor profileId={profileId} cif={DEMO_CIF} />
          } />
          <Route path="/results" element={<ComparisonResults />} />
          <Route path="/profile" element={
            <ProfilePage profileId={profileId} onLogout={logout} onProfileUpdated={handleProfileUpdated} />
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
      <BottomNav />
    </BrowserRouter>
  );
}

export function App() {
  return (
    <AuthProvider>
      <ActiveProfileProvider>
        <AppShell />
      </ActiveProfileProvider>
    </AuthProvider>
  );
}
