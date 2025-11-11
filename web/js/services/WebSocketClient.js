// WebSocketClient - WebSocket connection management
// Handles real-time event streaming with automatic reconnection

class WebSocketClient {
  constructor(url, eventStore) {
    this.url = url;
    this.eventStore = eventStore;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 30000; // 30 seconds
    this.reconnectTimer = null;
    this.isDestroyed = false;
  }

  connect() {
    if (this.isDestroyed) return;

    console.log(`[WebSocket] Connecting to ${this.url}`);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.reconnectAttempts = 0;
        this.eventStore.updateConnectionStatus('connected');
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
      };

      this.ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        this.eventStore.updateConnectionStatus('disconnected');

        // Attempt reconnection unless destroyed
        if (!this.isDestroyed) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      if (!this.isDestroyed) {
        this.scheduleReconnect();
      }
    }
  }

  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      console.log('[WebSocket] Message received:', message);

      if (message.type === 'event') {
        console.log('[WebSocket] New event received:', message.payload);
        this.eventStore.addEvent(message.payload);
      } else if (message.type === 'ping') {
        // Respond to ping with pong
        this.ws.send(JSON.stringify({ type: 'pong' }));
      } else if (message.type === 'health') {
        // Health update message
        console.log('[WebSocket] Health update:', message.payload);
      }
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
    }
  }

  scheduleReconnect() {
    if (this.isDestroyed) return;

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    console.log(`[WebSocket] Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts + 1})`);
    this.eventStore.updateConnectionStatus('reconnecting');

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  disconnect() {
    this.isDestroyed = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.eventStore.updateConnectionStatus('disconnected');
  }

  // Send a message to the server (if needed for future features)
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message: connection not open');
    }
  }
}

export default WebSocketClient;