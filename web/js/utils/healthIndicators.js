// Health Indicators Utility
// Determines health status (healthy/warning/critical) based on metric values

export function getHealthStatus(metric, value) {
  const thresholds = {
    cpu: { warning: 70, critical: 90 },
    memory: { warning: 80, critical: 90 },
    disk: { warning: 80, critical: 90 }
  };

  const threshold = thresholds[metric];
  if (!threshold) {
    console.warn(`[healthIndicators] Unknown metric: ${metric}`);
    return 'healthy';
  }

  if (value >= threshold.critical) return 'critical';
  if (value >= threshold.warning) return 'warning';
  return 'healthy';
}

export function getStatusColor(status) {
  const colors = {
    healthy: '#4caf50',   // Green
    warning: '#ff9800',   // Orange
    critical: '#f44336'   // Red
  };

  return colors[status] || colors.healthy;
}

export function getStatusLabel(status) {
  const labels = {
    healthy: 'Healthy',
    warning: 'Warning',
    critical: 'Critical'
  };

  return labels[status] || 'Unknown';
}