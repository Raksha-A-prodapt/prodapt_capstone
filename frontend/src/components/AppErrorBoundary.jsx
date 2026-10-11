import React from 'react';

export default class AppErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Frontend render error:', error, info);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <main className="app-container">
        <div className="card" style={{ borderColor: 'var(--color-error)' }}>
          <h1 className="page-title">The assistant could not render this response</h1>
          <p style={{ marginTop: '12px', color: 'var(--color-text)' }}>
            The API responded, but the browser received an unexpected response shape.
          </p>
          <pre style={{ marginTop: '12px', whiteSpace: 'pre-wrap', color: 'var(--color-error)' }}>
            {this.state.error?.message || String(this.state.error)}
          </pre>
          <button type="button" className="btn btn-primary" style={{ marginTop: '16px' }} onClick={this.handleReload}>
            Reload assistant
          </button>
        </div>
      </main>
    );
  }
}
