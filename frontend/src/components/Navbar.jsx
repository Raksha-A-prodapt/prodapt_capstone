import React, { useState } from 'react';
import UserMenu from './UserMenu';

export default function Navbar({ activePage, setActivePage, onSignOut }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'assistant', label: 'AI Assistant' },
    { id: 'prediction', label: 'Network Performance & Fault Prediction' },
    { id: 'comparison', label: 'Scenario Comparison' },
    { id: 'evaluations', label: 'Evaluations' },
  ];

  const handleNavClick = (pageId) => {
    setActivePage(pageId);
    setMobileMenuOpen(false);
  };

  return (
    <header
      style={{
        backgroundColor: 'var(--color-card)',
        borderBottom: '1px solid var(--color-border)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: '1360px',
          margin: '0 auto',
          padding: '0 20px',
          height: '62px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        {/* Left Side: Brand Logo and Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            type="button"
            onClick={() => handleNavClick('dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              textAlign: 'left',
            }}
            title="Go to Home Dashboard"
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                backgroundColor: 'var(--color-primary)',
                border: '1px solid var(--color-accent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-text)',
                fontWeight: 800,
                fontSize: '15px',
                flexShrink: 0,
              }}
            >
              📡
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span
                style={{
                  fontSize: '14.5px',
                  fontWeight: 700,
                  color: 'var(--color-text)',
                  letterSpacing: '-0.2px',
                }}
              >
                Telecom Network Operations Assistant
              </span>
              <span style={{ fontSize: '10.5px', color: 'var(--color-text-muted)' }}>
                5G NetOps Decision Support
              </span>
            </div>
          </button>

          {/* Small Home Shortcut */}
          <button
            type="button"
            onClick={() => handleNavClick('dashboard')}
            className="btn btn-secondary btn-xs"
            style={{
              marginLeft: '8px',
              backgroundColor: activePage === 'dashboard' ? 'var(--color-primary-subtle)' : 'transparent',
              borderColor: activePage === 'dashboard' ? 'var(--color-accent)' : 'var(--color-border)',
              color: activePage === 'dashboard' ? 'var(--color-accent)' : 'var(--color-text-muted)',
            }}
          >
            Home
          </button>
        </div>

        {/* Center: Three Primary Navigation Actions (Desktop) */}
        <nav
          className="desktop-nav"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {navItems.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item.id)}
                style={{
                  padding: '8px 14px',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 500,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid',
                  borderColor: isActive ? 'var(--color-accent)' : 'transparent',
                  backgroundColor: isActive ? 'var(--color-primary)' : 'transparent',
                  color: isActive ? 'var(--color-text)' : 'var(--color-text-muted)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = 'var(--color-text)';
                    e.currentTarget.style.backgroundColor = 'var(--color-input)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = 'var(--color-text-muted)';
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Right Side: User Menu & Mobile Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <UserMenu
            onNavigateToProfile={() => handleNavClick('profile')}
            onSignOut={onSignOut}
          />

          {/* Mobile hamburger button */}
          <button
            type="button"
            className="mobile-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              display: 'none',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 10px',
              color: 'var(--color-text)',
              cursor: 'pointer',
              fontSize: '16px',
            }}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div
          style={{
            borderTop: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-input)',
            padding: '12px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <button
            type="button"
            onClick={() => handleNavClick('dashboard')}
            style={{
              padding: '10px 12px',
              fontSize: '13px',
              textAlign: 'left',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: activePage === 'dashboard' ? 'var(--color-primary)' : 'transparent',
              color: activePage === 'dashboard' ? 'var(--color-text)' : 'var(--color-text-muted)',
              cursor: 'pointer',
            }}
          >
            Home
          </button>

          {navItems.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item.id)}
                style={{
                  padding: '10px 12px',
                  fontSize: '13px',
                  textAlign: 'left',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  backgroundColor: isActive ? 'var(--color-primary)' : 'transparent',
                  color: isActive ? 'var(--color-text)' : 'var(--color-text-muted)',
                  cursor: 'pointer',
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}

      <style>{`
        @media (max-width: 960px) {
          .desktop-nav {
            display: none !important;
          }
          .mobile-toggle {
            display: block !important;
          }
        }
      `}</style>
    </header>
  );
}
