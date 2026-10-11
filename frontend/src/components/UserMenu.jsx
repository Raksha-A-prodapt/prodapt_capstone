import React, { useState, useRef, useEffect } from 'react';

export default function UserMenu({ onNavigateToProfile, onSignOut }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={menuRef} style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: isOpen ? 'var(--color-input)' : 'transparent',
          border: '1px solid',
          borderColor: isOpen ? 'var(--color-primary)' : 'var(--color-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '6px 10px',
          color: 'var(--color-text)',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div
          style={{
            width: '26px',
            height: '26px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-text)',
            fontSize: '11px',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid var(--color-accent)',
          }}
        >
          DU
        </div>
        <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text)' }}>
          Demo User
        </span>
        <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s ease' }}>
          ▼
        </span>
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            width: '210px',
            backgroundColor: 'var(--color-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.7)',
            zIndex: 1000,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '12px 14px',
              borderBottom: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-input)',
            }}
          >
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)' }}>
              Demo User
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-accent)', marginTop: '2px' }}>
              Demo Session
            </div>
          </div>

          <div style={{ padding: '6px' }}>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                onNavigateToProfile();
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 10px',
                fontSize: '12.5px',
                color: 'var(--color-text)',
                background: 'transparent',
                border: 'none',
                borderRadius: '4px',
                textAlign: 'left',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-input)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <span>👤</span>
              <span>Profile</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                onSignOut();
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 10px',
                fontSize: '12.5px',
                color: 'var(--color-error)',
                background: 'transparent',
                border: 'none',
                borderRadius: '4px',
                textAlign: 'left',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-input)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <span>🚪</span>
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
