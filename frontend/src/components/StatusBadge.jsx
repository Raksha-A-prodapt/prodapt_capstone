import React from 'react';

export default function StatusBadge({ status, label, size = 'sm' }) {
  const normStatus = (status || '').toLowerCase();
  
  let badgeClass = 'badge-muted';
  let dotColor = '#8e9fb5';
  let displayLabel = label || status || 'Unknown';

  if (['success', 'ok', 'online', 'completed', 'good'].includes(normStatus)) {
    badgeClass = 'badge-success';
    dotColor = 'var(--color-accent)';
  } else if (['partial', 'warning', 'medium', 'fallback'].includes(normStatus)) {
    badgeClass = 'badge-warning';
    dotColor = 'var(--color-warning)';
  } else if (['error', 'failed', 'offline', 'high', 'critical'].includes(normStatus)) {
    badgeClass = 'badge-error';
    dotColor = 'var(--color-error)';
  } else if (['not_applicable', 'not_requested', 'skipped', 'none', 'idle'].includes(normStatus)) {
    badgeClass = 'badge-muted';
    dotColor = '#607274';
    if (!label && normStatus === 'not_applicable') displayLabel = 'Not Applicable';
    if (!label && normStatus === 'not_requested') displayLabel = 'Not Requested';
  } else if (['llm', 'info', 'running'].includes(normStatus)) {
    badgeClass = 'badge-teal';
    dotColor = 'var(--color-accent)';
  }

  return (
    <span className={`badge ${badgeClass}`} style={{ fontSize: size === 'xs' ? '10px' : '11px' }}>
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: dotColor,
          display: 'inline-block'
        }}
      />
      {displayLabel}
    </span>
  );
}
