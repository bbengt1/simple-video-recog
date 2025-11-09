# Web Dashboard (Phase 2)

**Responsibility:** Provides web UI for viewing events, filtering by time/camera, displaying annotated images, and real-time event notifications.

**Key Interfaces:**
- 5 core screens: Dashboard, Event Timeline, Event Detail, Settings, System Status
- WebSocket client for real-time updates
- REST API client for historical data

**Dependencies:**
- FastAPI server (REST API)
- WebSocket server (real-time events)

**Technology Stack:**
- Vanilla JavaScript ES6+, native CSS, no frameworks
- Module path: `web/` directory
- File structure: `index.html`, `app.js`, `styles.css`, `components/`, `services/`

**Implementation Notes:**
- SPA with hash-based routing (#/dashboard, #/events, etc.)
- Custom Observer pattern for state management
- Dark mode optimized for 4K displays
- Component-based architecture (functional approach)
- No build step - served directly from web/ directory
- API calls via fetch() with error handling

---
