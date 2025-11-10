// Dashboard Application JavaScript
// ES6 Modules for modern browser support

class DashboardApp {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.eventCount = 0;
        this.startTime = Date.now();
        this.uptimeInterval = null;

        // DOM elements
        this.loadingElement = document.getElementById('loading');
        this.dashboardElement = document.getElementById('dashboard');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.eventCountElement = document.getElementById('eventCount');
        this.uptimeElement = document.getElementById('uptime');
        this.wsStatusElement = document.getElementById('wsStatus');
        this.eventFeed = document.getElementById('eventFeed');
        this.sidebar = document.getElementById('sidebar');
        this.toggleSidebarBtn = document.getElementById('toggleSidebar');

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.startUptimeTimer();
        this.showDashboard();
    }

    setupEventListeners() {
        // Sidebar toggle
        if (this.toggleSidebarBtn) {
            this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // Window resize handling
        window.addEventListener('resize', () => this.handleResize());

        // Handle initial load
        window.addEventListener('load', () => {
            this.hideLoading();
        });

        // Handle online/offline events
        window.addEventListener('online', () => this.handleConnectionChange(true));
        window.addEventListener('offline', () => this.handleConnectionChange(false));
    }

    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/events`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                console.log('WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                console.log('WebSocket disconnected');

                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data);

            if (data.type === 'event') {
                this.handleNewEvent(data.payload);
            } else if (data.type === 'health') {
                this.handleHealthUpdate(data.payload);
            }

        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    handleNewEvent(eventData) {
        this.eventCount++;
        this.updateEventCount();

        // Add event to feed (placeholder for Story 5.5)
        this.addEventToFeed(eventData);

        // Show notification if page is not visible
        if (document.hidden) {
            this.showNotification('New event detected', eventData.description || 'Motion detected');
        }
    }

    handleHealthUpdate(healthData) {
        // Update metrics panel (placeholder for Story 5.6)
        console.log('Health update:', healthData);
        // TODO: Update metric cards with real data
    }

    addEventToFeed(eventData) {
        // Placeholder implementation - will be enhanced in Story 5.5
        const eventList = this.eventFeed.querySelector('.event-list');
        if (!eventList) return;

        // Remove skeleton loaders if present
        const skeletons = eventList.querySelectorAll('.skeleton');
        skeletons.forEach(skeleton => skeleton.remove());

        // Create event card (simplified version)
        const eventCard = document.createElement('div');
        eventCard.className = 'event-card';
        eventCard.innerHTML = `
            <div class="event-card-header">
                <h3 class="event-card-title">Event #${this.eventCount}</h3>
                <time class="event-card-time">${new Date().toLocaleTimeString()}</time>
            </div>
            <div class="event-card-content">
                <div class="event-card-image">
                    <span style="font-size: 2rem;">📹</span>
                </div>
                <div class="event-card-details">
                    <p class="event-card-description">${eventData.description || 'Motion detected in video stream'}</p>
                    <div class="event-card-objects">
                        <span class="object-tag">motion</span>
                    </div>
                </div>
            </div>
        `;

        // Add click handler for modal (Story 5.7)
        eventCard.addEventListener('click', () => this.showEventModal(eventData));

        // Insert at top of feed
        eventList.insertBefore(eventCard, eventList.firstChild);

        // Limit to 50 events to prevent memory issues
        const cards = eventList.querySelectorAll('.event-card');
        if (cards.length > 50) {
            eventList.removeChild(cards[cards.length - 1]);
        }
    }

    showEventModal(eventData) {
        // Placeholder for Story 5.7 - Event Detail Modal
        console.log('Show event modal for:', eventData);
        // TODO: Implement modal with full event details
    }

    updateConnectionStatus(connected) {
        this.isConnected = connected;

        if (this.connectionStatus) {
            const dot = this.connectionStatus.querySelector('.status-dot');
            const text = this.connectionStatus.querySelector('.status-text');

            if (connected) {
                dot.className = 'status-dot status-dot--success';
                text.textContent = 'Connected';
            } else {
                dot.className = 'status-dot status-dot--error';
                text.textContent = 'Disconnected';
            }
        }

        if (this.wsStatusElement) {
            this.wsStatusElement.textContent = `WebSocket: ${connected ? 'Connected' : 'Disconnected'}`;
            this.wsStatusElement.style.color = connected ? 'var(--accent-success)' : 'var(--accent-error)';
        }
    }

    updateEventCount() {
        if (this.eventCountElement) {
            this.eventCountElement.textContent = `${this.eventCount} events`;
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
        if (online && !this.isConnected) {
            // Attempt to reconnect WebSocket
            this.connectWebSocket();
        }

        this.showToast(
            online ? 'Connection restored' : 'Connection lost',
            online ? 'Internet connection has been restored.' : 'Internet connection has been lost.',
            online ? 'success' : 'error'
        );
    }

    showNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                icon: '/favicon.ico',
                tag: 'video-recognition-event'
            });
        } else if ('Notification' in window && Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, {
                        body: body,
                        icon: '/favicon.ico',
                        tag: 'video-recognition-event'
                    });
                }
            });
        }
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

    hideLoading() {
        // Ensure loading is hidden even if WebSocket takes time
        setTimeout(() => {
            if (this.loadingElement) {
                this.loadingElement.style.display = 'none';
            }
        }, 1000);
    }

    destroy() {
        // Cleanup
        if (this.ws) {
            this.ws.close();
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
    // Check for required browser features
    if (!window.WebSocket) {
        document.body.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 2rem; text-align: center;">
                <div>
                    <h1 style="color: #f44336; margin-bottom: 1rem;">Browser Not Supported</h1>
                    <p style="color: #666;">This dashboard requires a modern browser with WebSocket support.</p>
                    <p style="color: #666; margin-top: 1rem;">Please use Chrome 90+, Safari 14+, or Firefox 88+.</p>
                </div>
            </div>
        `;
        return;
    }

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