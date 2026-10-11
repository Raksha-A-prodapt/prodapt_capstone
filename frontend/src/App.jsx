import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DemoLogin from './components/DemoLogin';
import ProfilePanel from './components/ProfilePanel';
import HomeDashboard from './pages/HomeDashboard';
import AIAssistant from './pages/AIAssistant';
import PredictionDashboard from './pages/PredictionDashboard';
import ScenarioComparison from './pages/ScenarioComparison';
import Evaluations from './pages/Evaluations';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('telecom_demo_session') === 'true';
  });

  const [activePage, setActivePage] = useState('dashboard');

  const handleLoginSuccess = ({ username, mode }) => {
    localStorage.setItem('telecom_demo_session', 'true');
    localStorage.setItem('telecom_demo_user', username);
    setIsAuthenticated(true);
    setActivePage('dashboard');
  };

  const handleSignOut = () => {
    localStorage.removeItem('telecom_demo_session');
    localStorage.removeItem('telecom_demo_user');
    setIsAuthenticated(false);
    setActivePage('dashboard');
  };

  // If not authenticated, render DemoLogin only (Navbar hidden)
  if (!isAuthenticated) {
    return <DemoLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--color-background)' }}>
      {/* Top Navbar */}
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        onSignOut={handleSignOut}
      />

      {/* Main Page Area */}
      <main style={{ flex: 1 }}>
        {activePage === 'dashboard' && (
          <HomeDashboard onNavigate={(pageId) => setActivePage(pageId)} />
        )}
        {activePage === 'assistant' && <AIAssistant />}
        {activePage === 'prediction' && <PredictionDashboard />}
        {activePage === 'comparison' && <ScenarioComparison />}
        {activePage === 'evaluations' && <Evaluations />}
        {activePage === 'profile' && (
          <ProfilePanel
            onBackToDashboard={() => setActivePage('dashboard')}
            onSignOut={handleSignOut}
          />
        )}
      </main>

      {/* Compact Status Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--color-border)',
          backgroundColor: 'var(--color-card)',
          padding: '12px 20px',
          fontSize: '11.5px',
          color: 'var(--color-text-muted)',
        }}
      >
        <div
          style={{
            maxWidth: '1360px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <div>
            Telecom Network Operations Assistant &copy; 2026 &bull; Decision Support & Incident Triage
          </div>
          <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
            <span>API: <code style={{ color: 'var(--color-accent)' }}>http://127.0.0.1:8001</code></span>
            <span>UI: <code style={{ color: 'var(--color-accent)' }}>http://127.0.0.1:8790</code></span>
            <span>Synapt MCP: <code style={{ color: 'var(--color-accent)' }}>port 8000</code></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
