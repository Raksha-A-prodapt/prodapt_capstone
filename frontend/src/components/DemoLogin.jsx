import React, { useState } from 'react';

export default function DemoLogin({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});

  const handleSignIn = (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!username.trim()) {
      newErrors.username = 'Username is required';
    }
    if (!password.trim()) {
      newErrors.password = 'Password is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Success with provided credentials
    setErrors({});
    onLoginSuccess({ username: username.trim(), mode: 'credentials' });
  };

  const handleContinueAsDemo = () => {
    setErrors({});
    setUsername('demo.engineer');
    setPassword('telecom-ops-demo');
    onLoginSuccess({ username: 'demo.engineer', mode: 'demo_shortcut' });
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-background)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: '420px',
          width: '100%',
          backgroundColor: 'var(--color-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: '32px 28px',
          boxShadow: '0 12px 32px rgba(0, 0, 0, 0.8)',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              backgroundColor: 'var(--color-primary)',
              border: '1px solid var(--color-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              margin: '0 auto 16px',
            }}
          >
            📡
          </div>

          <h1
            style={{
              fontSize: '20px',
              fontWeight: 700,
              color: 'var(--color-text)',
              letterSpacing: '-0.3px',
              marginBottom: '6px',
            }}
          >
            Telecom Network Operations Assistant
          </h1>
          <p
            style={{
              fontSize: '13px',
              color: 'var(--color-text-muted)',
            }}
          >
            Network intelligence and troubleshooting workspace
          </p>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSignIn}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (errors.username) setErrors({ ...errors, username: null });
              }}
              placeholder="e.g. admin or demo.engineer"
              style={{
                borderColor: errors.username ? 'var(--color-error)' : 'var(--color-border)',
              }}
            />
            {errors.username && (
              <span style={{ fontSize: '11.5px', color: 'var(--color-error)', display: 'block', marginTop: '4px' }}>
                {errors.username}
              </span>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: '22px' }}>
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errors.password) setErrors({ ...errors, password: null });
              }}
              placeholder="••••••••••••"
              style={{
                borderColor: errors.password ? 'var(--color-error)' : 'var(--color-border)',
              }}
            />
            {errors.password && (
              <span style={{ fontSize: '11.5px', color: 'var(--color-error)', display: 'block', marginTop: '4px' }}>
                {errors.password}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '10px' }}>
              Sign In
            </button>

            <button
              type="button"
              onClick={handleContinueAsDemo}
              className="btn btn-subtle"
              style={{ width: '100%', padding: '10px' }}
            >
              Continue as Demo User →
            </button>
          </div>
        </form>

        {/* Sample Credentials & Demo Notice */}
        <div
          style={{
            marginTop: '24px',
            paddingTop: '16px',
            borderTop: '1px solid var(--color-border)',
            fontSize: '11.5px',
            color: 'var(--color-text-muted)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div>
            Sample demo credentials: <code style={{ color: 'var(--color-accent)' }}>admin</code> / <code style={{ color: 'var(--color-accent)' }}>telecom123</code>
          </div>
          <div
            style={{
              padding: '6px 10px',
              backgroundColor: 'var(--color-input)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              color: '#8a9999',
            }}
          >
            Demo access only — no real authentication
          </div>
        </div>
      </div>
    </div>
  );
}
