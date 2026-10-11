import React from 'react';

export default function KPICard({ label, value, unit, subtitle, icon, highlight = false }) {
  const formattedValue = typeof value === 'number'
    ? (Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2))
    : (value ?? '—');

  return (
    <div 
      className="card"
      style={{
        margin: 0,
        borderColor: highlight ? 'var(--color-primary)' : 'var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <span style={{ fontSize: '12px', color: 'var(--color-text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {label}
        </span>
        {icon && (
          <span style={{ color: highlight ? 'var(--color-accent)' : 'var(--color-primary)', fontSize: '16px' }}>
            {icon}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span style={{ fontSize: '24px', fontWeight: 700, color: highlight ? 'var(--color-accent)' : 'var(--color-text)', letterSpacing: '-0.5px' }}>
          {formattedValue}
        </span>
        {unit && (
          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            {unit}
          </span>
        )}
      </div>

      {subtitle && (
        <div style={{ fontSize: '11px', color: '#7a8c8c', marginTop: '6px' }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
