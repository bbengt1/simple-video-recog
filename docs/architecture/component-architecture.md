# Component Architecture

## Component Organization

```
web/
├── index.html                    # SPA entry point
├── app.js                        # Application bootstrap
├── styles.css                    # Global styles and dark mode theme
├── components/
│   ├── Dashboard.js              # Main dashboard view
│   ├── EventTimeline.js          # Event list with timeline
│   ├── EventCard.js              # Single event card component
│   ├── EventDetail.js            # Event detail modal/view
│   ├── Settings.js               # Settings form
│   ├── SystemStatus.js           # System health dashboard
│   ├── ImageViewer.js            # Annotated image viewer with zoom
│   ├── FilterBar.js              # Date/camera filter controls
│   └── Notification.js           # Toast notification component
├── services/
│   ├── apiClient.js              # REST API client wrapper
│   ├── websocketClient.js        # WebSocket client for real-time events
│   └── stateManager.js           # Custom Observer pattern state management
└── utils/
    ├── dateFormatter.js          # Date/time formatting utilities
    ├── router.js                 # Hash-based SPA routing
    └── imageHelper.js            # Image loading and caching
```

## Component Template (Functional Pattern)

```javascript
// components/EventCard.js
/**
 * EventCard component - Displays single event with thumbnail and metadata
 * @param {Event} event - Event object from API
 * @param {Function} onClick - Click handler for event detail navigation
 * @returns {HTMLElement} Rendered event card DOM element
 */
export function EventCard(event, onClick) {
  const card = document.createElement('div');
  card.className = 'event-card';
  card.setAttribute('data-event-id', event.event_id);

  card.innerHTML = `
    <div class="event-card__image">
      <img src="/api/v1/events/${event.event_id}/image"
           alt="${event.llm_description}"
           loading="lazy">
    </div>
    <div class="event-card__content">
      <div class="event-card__header">
        <span class="event-card__time">${formatTimestamp(event.timestamp)}</span>
        <span class="event-card__camera">${event.camera_id}</span>
      </div>
      <p class="event-card__description">${event.llm_description}</p>
      <div class="event-card__objects">
        ${event.detected_objects.map(obj =>
          `<span class="object-tag">${obj.label} (${(obj.confidence * 100).toFixed(0)}%)</span>`
        ).join('')}
      </div>
    </div>
  `;

  card.addEventListener('click', () => onClick(event.event_id));

  return card;
}

// Helper function
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}
```

**Component Pattern Guidelines:**
- Components are pure functions that return DOM elements
- No JSX - use template literals and DOM APIs
- Accept data and callbacks as parameters
- Return HTMLElement (not strings)
- Event listeners attached directly to elements
- CSS classes follow BEM naming convention

---
