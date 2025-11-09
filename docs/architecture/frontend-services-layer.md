# Frontend Services Layer

## API Client Setup

```javascript
// services/apiClient.js
/**
 * REST API client for backend communication
 * Centralized error handling and request configuration
 */

const BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json'
    }
  };

  try {
    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    // Handle different response types
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return await response.json();
    } else {
      return await response.blob(); // For images
    }
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    throw error;
  }
}

/**
 * Export typed API methods
 */
export const api = {
  health: () => apiRequest('/health'),

  metrics: () => apiRequest('/metrics'),

  events: {
    list: (filters = {}) => {
      const params = new URLSearchParams(filters);
      return apiRequest(`/events?${params}`);
    },

    getById: (eventId) => apiRequest(`/events/${eventId}`),

    getImage: (eventId) => apiRequest(`/events/${eventId}/image`)
  },

  config: () => apiRequest('/config')
};
```

## Service Example (WebSocket Client)

```javascript
// services/websocketClient.js
/**
 * WebSocket client for real-time event streaming
 */
import { appState } from './stateManager.js';

class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 8000; // 8 seconds
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'event') {
          this.handleNewEvent(message.data);
        } else if (message.type === 'error') {
          console.error('WebSocket error:', message.message);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };
  }

  reconnect() {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms...`);
    setTimeout(() => this.connect(), delay);
  }

  handleNewEvent(event) {
    // Prepend new event to state
    const currentEvents = appState.getState('events');
    appState.setState('events', [event, ...currentEvents]);

    // Show notification
    showNotification(`New event: ${event.llm_description}`);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Singleton instance
export const wsClient = new WebSocketClient('ws://localhost:8000/ws/events');

// Helper function for notifications
function showNotification(message) {
  // Implementation depends on Notification component
  console.log('Notification:', message);
}
```

---
