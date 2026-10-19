import React from 'react';
import { ApiStatusState } from '../types';

interface HealthStatusProps {
  statusState: ApiStatusState;
  onRefresh: () => void;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({ statusState, onRefresh }) => {
  const { health, readiness, isLoading, error, lastChecked } = statusState;

  const isHealthy = health?.status === 'ok';
  const isReady = readiness?.status === 'ready';

  return (
    <div className="card status-card">
      <div className="card-header">
        <div className="card-title">
          <span className={`status-indicator ${isHealthy ? 'status-online' : 'status-offline'}`} />
          <h3>System Health & Readiness</h3>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="btn btn-secondary"
          title="Refresh connection status"
        >
          {isLoading ? 'Checking...' : 'Refresh'}
        </button>
      </div>

      <div className="card-body">
        {error && (
          <div className="alert alert-error">
            <strong>Connection Error:</strong> {error}
            <div className="alert-hint">
              Ensure FastAPI backend is running on <code>http://localhost:8000</code>.
            </div>
          </div>
        )}

        <div className="status-grid">
          <div className="status-item">
            <span className="status-label">Backend Status</span>
            <span className={`status-badge ${isHealthy ? 'badge-success' : 'badge-danger'}`}>
              {isHealthy ? 'Operational' : 'Unavailable'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Storage Readiness</span>
            <span className={`status-badge ${isReady ? 'badge-success' : 'badge-warning'}`}>
              {isReady ? 'Ready' : 'Pending'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Application Version</span>
            <span className="status-value">{health?.version ?? '—'}</span>
          </div>

          <div className="status-item">
            <span className="status-label">Environment</span>
            <span className="status-value">{health?.environment ?? '—'}</span>
          </div>
        </div>

        {readiness?.services && (
          <div className="subservices-section">
            <h4>Component Breakdown</h4>
            <div className="subservices-list">
              {Object.entries(readiness.services).map(([serviceName, state]) => (
                <div key={serviceName} className="subservice-pill">
                  <span className="subservice-dot" />
                  <span className="subservice-name">{serviceName}:</span>
                  <span className="subservice-val">{state}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {lastChecked && (
          <div className="card-footer-text">
            Last checked: {new Date(lastChecked).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};
