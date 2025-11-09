# State Management Architecture

## State Structure (Custom Observer Pattern)

```javascript
// services/stateManager.js
/**
 * AppState - Centralized application state with Observer pattern
 * Notifies subscribers when state changes occur
 */
class AppState {
  constructor() {
    this.state = {
      events: [],
      filters: {
        startDate: null,
        endDate: null,
        cameraId: null
      },
      currentView: 'dashboard',
      selectedEventId: null,
      systemMetrics: null,
      isLoading: false,
      error: null
    };

    this.observers = new Map(); // Map<stateKey, Set<callback>>
  }

  /**
   * Subscribe to state changes for specific key
   * @param {string} key - State key to observe
   * @param {Function} callback - Called when state[key] changes
   * @returns {Function} Unsubscribe function
   */
  subscribe(key, callback) {
    if (!this.observers.has(key)) {
      this.observers.set(key, new Set());
    }
    this.observers.get(key).add(callback);

    // Return unsubscribe function
    return () => {
      this.observers.get(key).delete(callback);
    };
  }

  /**
   * Update state and notify observers
   * @param {string} key - State key to update
   * @param {*} value - New value
   */
  setState(key, value) {
    const oldValue = this.state[key];
    this.state[key] = value;

    // Notify observers only if value changed
    if (oldValue !== value && this.observers.has(key)) {
      this.observers.get(key).forEach(callback => {
        callback(value, oldValue);
      });
    }
  }

  /**
   * Get current state value
   * @param {string} key - State key
   * @returns {*} Current value
   */
  getState(key) {
    return this.state[key];
  }

  /**
   * Batch update multiple state keys
   * @param {Object} updates - Key-value pairs to update
   */
  batchUpdate(updates) {
    Object.entries(updates).forEach(([key, value]) => {
      this.setState(key, value);
    });
  }
}

// Singleton instance
export const appState = new AppState();
```

## State Management Patterns

**Pattern 1: Component subscribes to state**
```javascript
// components/EventTimeline.js
import { appState } from '../services/stateManager.js';

export function EventTimeline() {
  const container = document.createElement('div');
  container.className = 'event-timeline';

  // Subscribe to events state
  const unsubscribe = appState.subscribe('events', (newEvents) => {
    renderEvents(container, newEvents);
  });

  // Initial render
  renderEvents(container, appState.getState('events'));

  // Cleanup on component removal
  container.addEventListener('remove', unsubscribe);

  return container;
}
```

**Pattern 2: API call updates state**
```javascript
// services/apiClient.js
import { appState } from './stateManager.js';

export async function fetchEvents(filters = {}) {
  appState.setState('isLoading', true);

  try {
    const queryParams = new URLSearchParams(filters);
    const response = await fetch(`/api/v1/events?${queryParams}`);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    appState.setState('events', data.events);
    appState.setState('error', null);
  } catch (error) {
    appState.setState('error', error.message);
    console.error('Failed to fetch events:', error);
  } finally {
    appState.setState('isLoading', false);
  }
}
```

**Pattern 3: User interaction triggers state change**
```javascript
// components/FilterBar.js
import { appState } from '../services/stateManager.js';
import { fetchEvents } from '../services/apiClient.js';

export function FilterBar() {
  const form = document.createElement('form');
  form.className = 'filter-bar';

  form.innerHTML = `
    <input type="date" name="startDate" id="filter-start">
    <input type="date" name="endDate" id="filter-end">
    <button type="submit">Apply Filters</button>
  `;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    const filters = {
      startDate: formData.get('startDate'),
      endDate: formData.get('endDate')
    };

    appState.setState('filters', filters);
    fetchEvents(filters); // Triggers API call, which updates events state
  });

  return form;
}
```

---
