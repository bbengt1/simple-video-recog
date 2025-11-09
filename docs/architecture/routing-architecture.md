# Routing Architecture

## Route Organization (Hash-based Routing)

```javascript
// utils/router.js
/**
 * Simple hash-based router for SPA navigation
 * Routes map to component factory functions
 */
import { Dashboard } from '../components/Dashboard.js';
import { EventTimeline } from '../components/EventTimeline.js';
import { EventDetail } from '../components/EventDetail.js';
import { Settings } from '../components/Settings.js';
import { SystemStatus } from '../components/SystemStatus.js';

const routes = {
  '': Dashboard,           // #/ or #
  'dashboard': Dashboard,  // #/dashboard
  'events': EventTimeline, // #/events
  'event': EventDetail,    // #/event/:id
  'settings': Settings,    // #/settings
  'status': SystemStatus   // #/status
};

/**
 * Parse hash and extract route + params
 * Example: #/event/evt_12345 -> { route: 'event', params: { id: 'evt_12345' } }
 */
function parseHash() {
  const hash = window.location.hash.slice(1) || '/';
  const [path, ...paramParts] = hash.split('/').filter(Boolean);

  return {
    route: path || '',
    params: {
      id: paramParts[0] || null
    }
  };
}

/**
 * Render component for current route
 */
function render() {
  const { route, params } = parseHash();
  const Component = routes[route] || routes[''];

  const appRoot = document.getElementById('app');
  appRoot.innerHTML = ''; // Clear previous content
  appRoot.appendChild(Component(params));
}

/**
 * Navigate to route programmatically
 * @param {string} path - Route path (e.g., '/events', '/event/evt_12345')
 */
export function navigate(path) {
  window.location.hash = path;
}

/**
 * Initialize router
 */
export function initRouter() {
  window.addEventListener('hashchange', render);
  window.addEventListener('load', render);
}
```

## Navigation Example

```javascript
// components/EventCard.js
import { navigate } from '../utils/router.js';

export function EventCard(event, onClick) {
  // ...
  card.addEventListener('click', () => {
    navigate(`/event/${event.event_id}`);
  });
  // ...
}
```

---
