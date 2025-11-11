// Dashboard Application - Main entry point
// Initializes all components and manages application lifecycle

import eventStore from './state/EventStore.js';
import WebSocketClient from './services/WebSocketClient.js';
import EventFeed from './components/EventFeed.js';
import ApiClient from './services/ApiClient.js';

class DashboardApp {
    constructor() {
        this.wsClient = null;
        this.eventFeed = null;
        this.apiClient = new ApiClient();
        this.startTime = Date.now();
        this.uptimeInterval = null;

        // DOM elements
        this.loadingElement = document.getElementById('loading');
        this.dashboardElement = document.getElementById('dashboard');
        this.connectionStatus = document.querySelector('.header-status .status-indicator');
        this.eventCountElement = document.getElementById('eventCount');
        this.uptimeElement = document.getElementById('uptime');
        this.wsStatusElement = document.getElementById('wsStatus');
        this.sidebar = document.getElementById('sidebar');
        this.toggleSidebarBtn = document.getElementById('toggleSidebar');

        this.init();
    }

    async init() {
        console.log('[App] Initializing dashboard...');

        // Check for required browser features
        if (!window.WebSocket) {
            this.showBrowserNotSupported();
            return;
        }

        this.setupEventListeners();

        // Initialize event feed component
        this.eventFeed = new EventFeed('.event-list');

        // Load initial events from REST API
        await this.eventFeed.loadInitialEvents();

        // Connect to WebSocket for real-time updates
        this.wsClient = new WebSocketClient('ws://localhost:8000/ws/events', eventStore);
        this.wsClient.connect();

        // Subscribe to connection status for header update
        eventStore.subscribe((state) => {
            this.updateConnectionStatus(state.connectionStatus);
            this.updateEventCount(state.events.length);
        });

        // Start uptime timer
        this.startUptimeTimer();

        // Show dashboard
        this.showDashboard();

        console.log('[App] Dashboard ready');
    }

    setupEventListeners() {
        // Sidebar toggle
        if (this.toggleSidebarBtn) {
            this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // Window resize handling
        window.addEventListener('resize', () => this.handleResize());

        // Handle online/offline events
        window.addEventListener('online', () => this.handleConnectionChange(true));
        window.addEventListener('offline', () => this.handleConnectionChange(false));
    }

    updateConnectionStatus(status) {
        if (!this.connectionStatus) return;

        const dot = this.connectionStatus.querySelector('.status-dot');
        const text = this.connectionStatus.querySelector('.status-text');

        if (!dot || !text) return;

        // Remove all status classes
        dot.classList.remove('status-dot--success', 'status-dot--warning', 'status-dot--error');

        switch (status) {
            case 'connected':
                dot.classList.add('status-dot--success');
                text.textContent = 'Connected';
                break;
            case 'reconnecting':
                dot.classList.add('status-dot--warning');
                text.textContent = 'Reconnecting...';
                break;
            case 'disconnected':
            default:
                dot.classList.add('status-dot--error');
                text.textContent = 'Disconnected';
                break;
        }

        // Update footer WebSocket status
        if (this.wsStatusElement) {
            this.wsStatusElement.textContent = `WebSocket: ${text.textContent}`;
            this.wsStatusElement.style.color = status === 'connected' ? 'var(--accent-success)' : 'var(--accent-error)';
        }
    }

    updateEventCount(count) {
        if (this.eventCountElement) {
            this.eventCountElement.textContent = `${count} events`;
        }
    }

    startUptimeTimer() {
        this.uptimeInterval = setInterval(() => {
            const uptime = Math.floor((Date.now() - this.startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);

            if (this.uptimeElement) {
                this.uptimeElement.textContent = `Uptime: ${hours}h ${minutes}m`;
            }
        }, 60000); // Update every minute
    }

    toggleSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.toggle('sidebar--collapsed');
        }
    }

    handleResize() {
        // Handle responsive layout changes
        const width = window.innerWidth;

        if (width < 768) {
            // Mobile: collapse sidebar automatically
            if (this.sidebar && !this.sidebar.classList.contains('sidebar--collapsed')) {
                this.sidebar.classList.add('sidebar--collapsed');
            }
        }
    }

    handleConnectionChange(online) {
        if (online && eventStore.getState().connectionStatus === 'disconnected') {
            // Attempt to reconnect WebSocket
            if (this.wsClient) {
                this.wsClient.connect();
            }
        }

        this.showToast(
            online ? 'Connection restored' : 'Connection lost',
            online ? 'Internet connection has been restored.' : 'Internet connection has been lost.',
            online ? 'success' : 'error'
        );
    }

    showToast(title, message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" aria-label="Close notification">×</button>
        `;

        // Add close handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            toast.remove();
        });

        // Add to container
        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    showDashboard() {
        // Hide loading and show dashboard
        if (this.loadingElement) {
            this.loadingElement.style.display = 'none';
        }

        if (this.dashboardElement) {
            this.dashboardElement.style.display = 'grid';
        }
    }

    showBrowserNotSupported() {
        document.body.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 2rem; text-align: center;">
                <div>
                    <h1 style="color: #f44336; margin-bottom: 1rem;">Browser Not Supported</h1>
                    <p style="color: #666;">This dashboard requires a modern browser with WebSocket support.</p>
                    <p style="color: #666; margin-top: 1rem;">Please use Chrome 90+, Safari 14+, or Firefox 88+.</p>
                </div>
            </div>
        `;
    }

    destroy() {
        // Cleanup
        if (this.wsClient) {
            this.wsClient.disconnect();
        }

        if (this.eventFeed) {
            this.eventFeed.destroy();
        }

        if (this.uptimeInterval) {
            clearInterval(this.uptimeInterval);
        }

        // Remove event listeners
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('online', this.handleConnectionChange);
        window.removeEventListener('offline', this.handleConnectionChange);
    }
}

// Initialize the dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the dashboard app
    window.dashboardApp = new DashboardApp();

    // Handle page visibility changes for notifications
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            document.title = '(Inactive) Video Recognition Dashboard';
        } else {
            document.title = 'Video Recognition Dashboard';
        }
    });
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboardApp) {
        window.dashboardApp.destroy();
    }
});

// Export for potential future module usage
export default DashboardApp;