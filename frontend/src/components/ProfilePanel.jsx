import React from 'react';

export default function ProfilePanel({ onBackToDashboard, onSignOut }) {
  return (
    <div className="app-container" style={{ maxWidth: '680px' }}>
      <div style={{ marginBottom: '20px' }}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className="btn btn-secondary btn-sm"
        >
          ← Back to Dashboard
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">User Profile</div>
            <div className="card-subtitle">Local demo session details</div>
          </div>
          <span className="badge badge-teal">Demo Session</span>
        </div>

        {/* Profile Avatar & Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '24px' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary)',
              border: '2px solid var(--color-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              fontWeight: 700,
              color: 'var(--color-text)',
            }}
          >
            DU
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>
              Demo User
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--color-accent)', marginTop: '2px' }}>
              Network Operations Engineer
            </p>
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
              Role: Tier-2 NOC / Diagnostic Analyst
            </p>
          </div>
        </div>

        {/* Details Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '12px',
            backgroundColor: 'var(--color-input)',
            padding: '16px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border)',
            marginBottom: '20px',
          }}
        >
          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block' }}>
              Account Type
            </span>
            <span style={{ fontSize: '13px', color: 'var(--color-text)', fontWeight: 500 }}>
              Demo Session
            </span>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block' }}>
              Authentication Mode
            </span>
            <span style={{ fontSize: '13px', color: 'var(--color-text)', fontWeight: 500 }}>
              Frontend demo
            </span>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block' }}>
              API Environment
            </span>
            <span style={{ fontSize: '13px', color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
              127.0.0.1:8001
            </span>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block' }}>
              Session Storage
            </span>
            <span style={{ fontSize: '13px', color: 'var(--color-text)', fontWeight: 500 }}>
              Browser Local Storage (Mock)
            </span>
          </div>
        </div>

        {/* Informational Notice */}
        <div className="alert alert-info" style={{ marginBottom: '24px' }}>
          <span>ℹ️</span>
          <div>
            <strong>Demonstration Notice:</strong> This profile is maintained in local browser state for demonstration purposes. 
            No sensitive credentials or real authentication tokens are exchanged or stored on any server.
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            type="button"
            onClick={onBackToDashboard}
            className="btn btn-primary"
          >
            Return to Dashboard
          </button>

          <button
            type="button"
            onClick={onSignOut}
            className="btn btn-secondary"
            style={{ color: 'var(--color-error)', borderColor: 'rgba(239, 68, 68, 0.4)' }}
          >
            Sign Out of Demo
          </button>
        </div>
      </div>
    </div>
  );
}
