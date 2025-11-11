// MetricsPanel Component
// Displays system health metrics, event statistics, and camera activity

import ApiClient from '../services/ApiClient.js';
import { formatBytes, formatPercentage, formatUptime, formatNumber } from '../utils/formatters.js';
import { getHealthStatus } from '../utils/healthIndicators.js';

class MetricsPanel {
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    if (!this.container) {
      throw new Error(`Container not found: ${containerSelector}`);
    }

    this.apiClient = new ApiClient();
    this.pollInterval = null;
    this.pollFrequency = 5000; // 5 seconds
    this.isVisible = true;
    this.lastMetrics = null; // Store last successful metrics (for stale data)

    // Setup Page Visibility API
    this.setupVisibilityListener();

    console.log('[MetricsPanel] Initialized');
  }

  async init() {
    console.log('[MetricsPanel] Fetching initial metrics...');

    // Initial load
    await this.fetchAndRenderMetrics();

    // Start polling
    this.startPolling();
  }

  async fetchAndRenderMetrics() {
    try {
      const metrics = await this.apiClient.getMetrics();
      this.lastMetrics = metrics; // Store for stale data fallback
      this.render(metrics);
      this.updateLastUpdated();
    } catch (error) {
      console.error('[MetricsPanel] Failed to fetch metrics:', error);

      if (this.lastMetrics) {
        // Show stale data with warning
        this.renderStaleDataWarning();
      } else {
        // No previous data, show error
        this.showError();
      }
    }
  }

  startPolling() {
    console.log('[MetricsPanel] Starting polling (every 5s)');

    this.pollInterval = setInterval(() => {
      if (this.isVisible) {
        this.fetchAndRenderMetrics();
      } else {
        console.log('[MetricsPanel] Tab hidden, skipping poll');
      }
    }, this.pollFrequency);
  }

  stopPolling() {
    console.log('[MetricsPanel] Stopping polling');
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  setupVisibilityListener() {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        console.log('[MetricsPanel] Tab hidden, pausing polling');
        this.isVisible = false;
      } else {
        console.log('[MetricsPanel] Tab visible, resuming polling');
        this.isVisible = true;
        // Fetch immediately when tab becomes visible
        this.fetchAndRenderMetrics();
      }
    });
  }

  render(metrics) {
    // Clear container
    this.container.innerHTML = '';

    // Disk Space Warning (if critical)
    if (metrics.system.disk_usage_percent > 90) {
      const warning = this.createDiskWarning(metrics.system.disk_usage_percent);
      this.container.appendChild(warning);
    }

    // System Health Section
    const systemSection = this.createSystemHealthSection(metrics.system);
    this.container.appendChild(systemSection);

    // Event Statistics Section
    const eventsSection = this.createEventStatisticsSection(metrics.events);
    this.container.appendChild(eventsSection);

    // Camera Activity Section
    if (metrics.cameras && metrics.cameras.length > 0) {
      const camerasSection = this.createCameraActivitySection(metrics.cameras);
      this.container.appendChild(camerasSection);
    }
  }

  createSystemHealthSection(system) {
    const section = document.createElement('section');
    section.className = 'metrics-section';
    section.setAttribute('aria-label', 'System Health');

    const header = document.createElement('h3');
    header.textContent = 'System Health';
    section.appendChild(header);

    // CPU Usage
    const cpuMetric = this.createMetric(
      'CPU Usage',
      formatPercentage(system.cpu_usage_percent),
      system.cpu_usage_percent,
      getHealthStatus('cpu', system.cpu_usage_percent)
    );
    section.appendChild(cpuMetric);

    // Memory Usage
    const memoryPercent = (system.memory_used / system.memory_total) * 100;
    const memoryMetric = this.createMetric(
      'Memory Usage',
      `${formatBytes(system.memory_used)} / ${formatBytes(system.memory_total)}`,
      memoryPercent,
      getHealthStatus('memory', memoryPercent)
    );
    section.appendChild(memoryMetric);

    // Disk Usage
    const diskMetric = this.createMetric(
      'Disk Usage',
      `${formatBytes(system.disk_used)} / ${formatBytes(system.disk_total)}`,
      system.disk_usage_percent,
      getHealthStatus('disk', system.disk_usage_percent)
    );
    section.appendChild(diskMetric);

    // System Uptime
    const uptimeDiv = document.createElement('div');
    uptimeDiv.className = 'metric-simple';
    uptimeDiv.innerHTML = `
      <span class="metric-label">System Uptime</span>
      <span class="metric-value">${formatUptime(system.system_uptime_seconds)}</span>
    `;
    section.appendChild(uptimeDiv);

    // App Uptime
    const appUptimeDiv = document.createElement('div');
    appUptimeDiv.className = 'metric-simple';
    appUptimeDiv.innerHTML = `
      <span class="metric-label">App Uptime</span>
      <span class="metric-value">${formatUptime(system.app_uptime_seconds)}</span>
    `;
    section.appendChild(appUptimeDiv);

    return section;
  }

  createEventStatisticsSection(events) {
    const section = document.createElement('section');
    section.className = 'metrics-section';
    section.setAttribute('aria-label', 'Event Statistics');

    const header = document.createElement('h3');
    header.textContent = 'Event Statistics';
    section.appendChild(header);

    // Total Events
    const totalDiv = document.createElement('div');
    totalDiv.className = 'metric-simple';
    totalDiv.innerHTML = `
      <span class="metric-label">Total Events</span>
      <span class="metric-value">${formatNumber(events.total_events)}</span>
    `;
    section.appendChild(totalDiv);

    // Events Today
    const todayDiv = document.createElement('div');
    todayDiv.className = 'metric-simple';
    todayDiv.innerHTML = `
      <span class="metric-label">Events Today</span>
      <span class="metric-value">${formatNumber(events.events_today)}</span>
    `;
    section.appendChild(todayDiv);

    // Events This Hour
    const hourDiv = document.createElement('div');
    hourDiv.className = 'metric-simple';
    hourDiv.innerHTML = `
      <span class="metric-label">Events This Hour</span>
      <span class="metric-value">${formatNumber(events.events_this_hour)}</span>
    `;
    section.appendChild(hourDiv);

    // Detection Rate (with trend)
    const trend = this.getTrendIndicator(
      events.events_per_hour_avg,
      events.events_per_hour_previous
    );
    const rateDiv = document.createElement('div');
    rateDiv.className = 'metric-simple';
    rateDiv.innerHTML = `
      <span class="metric-label">Detection Rate</span>
      <span class="metric-value">${events.events_per_hour_avg.toFixed(1)}/hr ${trend}</span>
    `;
    section.appendChild(rateDiv);

    return section;
  }

  createCameraActivitySection(cameras) {
    const section = document.createElement('section');
    section.className = 'metrics-section';
    section.setAttribute('aria-label', 'Camera Activity');

    const header = document.createElement('h3');
    header.textContent = 'Camera Activity';
    section.appendChild(header);

    cameras.forEach(camera => {
      const cameraDiv = document.createElement('div');
      cameraDiv.className = 'camera-metric';

      const status = this.getCameraStatus(camera.last_event_time);
      const statusDot = `<span class="status-dot ${status}"></span>`;

      const lastSeen = camera.last_event_time
        ? this.formatLastSeen(camera.last_event_time)
        : 'No events';

      cameraDiv.innerHTML = `
        ${statusDot}
        <div class="camera-info">
          <div class="camera-name">${camera.camera_id}</div>
          <div class="camera-stats">
            ${formatNumber(camera.event_count)} events • ${lastSeen}
          </div>
        </div>
      `;

      section.appendChild(cameraDiv);
    });

    return section;
  }

  createMetric(label, value, percentage, status) {
    const metricDiv = document.createElement('div');
    metricDiv.className = 'metric-with-bar';
    metricDiv.setAttribute('role', 'progressbar');
    metricDiv.setAttribute('aria-label', `${label}: ${value}, status ${status}`);
    metricDiv.setAttribute('aria-valuenow', Math.round(percentage));
    metricDiv.setAttribute('aria-valuemin', '0');
    metricDiv.setAttribute('aria-valuemax', '100');

    const statusDot = `<span class="status-dot ${status}"></span>`;

    metricDiv.innerHTML = `
      <div class="metric-header">
        ${statusDot}
        <span class="metric-label">${label}</span>
        <span class="metric-value">${value}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill ${status}" style="width: ${percentage}%"></div>
      </div>
    `;

    return metricDiv;
  }

  createDiskWarning(diskUsagePercent) {
    const warning = document.createElement('div');
    warning.className = 'alert alert-danger';
    warning.setAttribute('role', 'alert');
    warning.setAttribute('aria-live', 'assertive');

    warning.innerHTML = `
      <div class="alert-icon">⚠️</div>
      <div class="alert-content">
        <strong>Low disk space</strong>
        <p>${diskUsagePercent.toFixed(0)}% used. Clear old recordings to free space.</p>
      </div>
    `;

    return warning;
  }

  getTrendIndicator(current, previous) {
    if (!previous || previous === 0) return '';

    const change = ((current - previous) / previous) * 100;

    if (change > 10) {
      return '<span class="trend trend-up" aria-label="increasing">↑</span>';
    } else if (change < -10) {
      return '<span class="trend trend-down" aria-label="decreasing">↓</span>';
    } else {
      return '<span class="trend trend-stable" aria-label="stable">→</span>';
    }
  }

  getCameraStatus(lastEventTime) {
    if (!lastEventTime) return 'offline';

    const now = new Date();
    const lastEvent = new Date(lastEventTime);
    const minutesSince = (now - lastEvent) / (1000 * 60);

    if (minutesSince < 5) return 'active';   // Green
    if (minutesSince < 60) return 'idle';    // Yellow
    return 'offline';                         // Red
  }

  formatLastSeen(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  }

  updateLastUpdated() {
    let lastUpdated = this.container.querySelector('.last-updated');

    if (!lastUpdated) {
      lastUpdated = document.createElement('div');
      lastUpdated.className = 'last-updated';
      this.container.appendChild(lastUpdated);
    }

    const now = new Date();
    lastUpdated.textContent = `Updated: ${now.toLocaleTimeString()}`;
    lastUpdated.setAttribute('aria-live', 'polite');
  }

  renderStaleDataWarning() {
    // Show existing data with stale warning
    if (this.lastMetrics) {
      this.render(this.lastMetrics);

      // Add stale data warning
      const warning = document.createElement('div');
      warning.className = 'alert alert-warning';
      warning.innerHTML = `
        <div class="alert-icon">⚠️</div>
        <div class="alert-content">
          <strong>Connection issue</strong>
          <p>Showing cached data. <button class="btn-retry" onclick="window.metricsPanel.fetchAndRenderMetrics()">Retry</button></p>
        </div>
      `;
      this.container.insertBefore(warning, this.container.firstChild);
    }
  }

  showError() {
    this.container.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <h3>Unable to load metrics</h3>
        <p>The metrics endpoint is not responding.</p>
        <button class="btn-retry" onclick="window.metricsPanel.fetchAndRenderMetrics()">Retry</button>
      </div>
    `;
  }

  destroy() {
    console.log('[MetricsPanel] Destroying...');
    this.stopPolling();
  }
}

export default MetricsPanel;