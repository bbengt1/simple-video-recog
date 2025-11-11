// EventStore - State Management with Observer Pattern
// Manages application state for events and connection status

class EventStore {
  constructor() {
    this.events = [];
    this.connectionStatus = 'disconnected';
    this.subscribers = [];
    this.maxEvents = 500; // Memory limit to prevent memory leaks
  }

  // Observer Pattern: Subscribe to state changes
  subscribe(callback) {
    this.subscribers.push(callback);

    // Return unsubscribe function
    return () => {
      this.subscribers = this.subscribers.filter(sub => sub !== callback);
    };
  }

  // Notify all subscribers of state change
  notify() {
    const state = {
      events: this.events,
      connectionStatus: this.connectionStatus
    };

    this.subscribers.forEach(callback => callback(state));
  }

  // Add new event (from WebSocket or REST API)
  addEvent(event) {
    // Check if event already exists (prevent duplicates)
    const exists = this.events.some(e => e.event_id === event.event_id);
    if (exists) {
      console.log('[EventStore] Duplicate event ignored:', event.event_id);
      return;
    }

    // Add to beginning (newest first)
    this.events.unshift(event);

    // Enforce memory limit
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(0, this.maxEvents);
      console.log(`[EventStore] Trimmed to ${this.maxEvents} events`);
    }

    this.notify();
  }

  // Add multiple events (from REST API)
  addEvents(events) {
    events.forEach(event => {
      // Check if event already exists
      const exists = this.events.some(e => e.event_id === event.event_id);
      if (!exists) {
        this.events.push(event);
      }
    });

    // Sort by timestamp (newest first)
    this.events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    // Enforce memory limit
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(0, this.maxEvents);
    }

    this.notify();
  }

  // Update connection status
  updateConnectionStatus(status) {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status;
      this.notify();
    }
  }

  // Get current state
  getState() {
    return {
      events: this.events,
      connectionStatus: this.connectionStatus
    };
  }

  // Clear all events (useful for testing or reset)
  clearEvents() {
    this.events = [];
    this.notify();
  }
}

// Singleton instance
const eventStore = new EventStore();

export default eventStore;