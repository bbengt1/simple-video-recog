# Epic 5: Web Dashboard & Real-Time Monitoring

**Epic Status:** Draft
**Priority:** High
**Estimated Effort:** 8-12 weeks
**Business Value:** Enables real-time monitoring and investigation of video recognition events

## Epic Overview

**As a** home security user,
**I want** a web-based dashboard to monitor video recognition events in real-time,
**so that** I can quickly understand what's happening in my monitored spaces without checking logs or files.

## Business Context

With the MVP complete, users can now capture and analyze video events, but they lack an intuitive way to monitor and investigate events in real-time. The web dashboard transforms the system from a "black box" logging tool into an interactive monitoring platform that enables:

- **Real-time awareness** of security events as they happen
- **Quick investigation** of events with visual evidence
- **System health monitoring** to ensure reliable operation
- **Historical analysis** of patterns and trends

## Success Criteria

- Users can access a web dashboard at `http://localhost:8080` (configurable port)
- Dashboard shows live event feed with thumbnails and descriptions
- System health metrics are displayed in real-time
- Event details include annotated images and full metadata
- Dashboard works on desktop browsers (Chrome, Safari, Firefox)
- No external dependencies or CDNs required
- Dashboard loads in <3 seconds on modern hardware

## Requirements

### Functional Requirements

#### FR32: Web Server & API
The system SHALL provide a local web server serving static HTML/CSS/JS assets and REST API endpoints for data access.

**Acceptance Criteria:**
- Web server starts automatically with main application (`--web` flag)
- Configurable port (default: 8080)
- Serves dashboard at root path `/`
- API endpoints under `/api/` prefix
- No external network dependencies

#### FR33: Real-Time Event Feed
The dashboard SHALL display a live feed of video recognition events as they occur.

**Acceptance Criteria:**
- Events appear within 2 seconds of detection
- Each event shows: timestamp, thumbnail, semantic description, detected objects
- Auto-scrolling feed (newest events at top)
- Pause/resume functionality for investigation
- Maximum 100 events in live feed (pagination for older events)

#### FR34: Event Detail View
Users SHALL be able to click events to see full details including annotated images.

**Acceptance Criteria:**
- Modal or dedicated page showing full event details
- High-resolution annotated image with bounding boxes
- Complete JSON metadata (formatted and collapsible)
- LLM semantic description prominently displayed
- Navigation to previous/next events

#### FR35: System Health Dashboard
The dashboard SHALL display real-time system performance metrics.

**Acceptance Criteria:**
- CPU usage percentage
- Memory usage (RAM)
- Inference times (CoreML, LLM)
- Event processing rate (events/minute)
- Frame capture rate (FPS)
- System uptime and availability
- Color-coded status indicators (green/yellow/red)

#### FR36: Search & Filtering
Users SHALL be able to search and filter historical events.

**Acceptance Criteria:**
- Time range filters (last hour, 24hr, 7 days, custom)
- Object type filtering (person, vehicle, animal, etc.)
- Confidence threshold slider
- Free-text search in semantic descriptions
- Results update in real-time as filters change

### Non-Functional Requirements

#### NFR31: Performance
- Dashboard SHALL load in <3 seconds
- API responses SHALL be <500ms for event queries
- WebSocket/SSE updates SHALL have <1 second latency
- Memory usage SHALL remain <200MB for dashboard operation

#### NFR32: Security
- Dashboard SHALL only be accessible from localhost/127.0.0.1
- No authentication required (local-only system)
- HTTPS not required (localhost only)

#### NFR33: Browser Compatibility
- SHALL work on Chrome 90+, Safari 14+, Firefox 88+
- Responsive design for desktop (minimum 1280px width)
- Graceful degradation for older browsers

## Technical Approach

### Architecture Decisions

**Web Framework:** FastAPI for async web server with automatic OpenAPI docs
**Frontend:** Vanilla JavaScript (HTML/CSS/JS) - no frameworks to minimize dependencies
**Real-Time Updates:** Server-Sent Events (SSE) for live event streaming
**Data Access:** REST API endpoints for event queries and system metrics
**Styling:** CSS Grid/Flexbox with custom design system

### Implementation Strategy

1. **API Server** (`api/` directory)
   - FastAPI application with CORS middleware
   - Event streaming endpoint with SSE
   - REST endpoints for event queries and metrics
   - Static file serving for dashboard assets

2. **Web Dashboard** (`web/` directory)
   - Single-page application structure
   - Modular JavaScript for event feed, details, search
   - CSS for responsive dashboard layout
   - WebSocket/SSE client for real-time updates

3. **Integration Points**
   - Event persistence system provides data access
   - Metrics collector feeds system health data
   - Image storage serves annotated thumbnails

## Story Breakdown

### Story 5.1: FastAPI Server Setup
**As a** developer,
**I want** a FastAPI web server integrated with the main application,
**so that** I can serve the dashboard and provide API endpoints.

### Story 5.2: Event API Endpoints
**As a** frontend developer,
**I want** REST API endpoints for querying events,
**so that** the dashboard can display historical and live events.

### Story 5.3: Real-Time Event Streaming
**As a** user,
**I want** live event updates without page refresh,
**so that** I can monitor events in real-time.

### Story 5.4: Dashboard HTML/CSS Framework
**As a** developer,
**I want** the basic dashboard HTML and CSS structure,
**so that** I can build the interactive components.

### Story 5.5: Event Feed Component
**As a** user,
**I want** to see a scrolling list of recent events,
**so that** I can quickly scan recent activity.

### Story 5.6: System Health Display
**As a** user,
**I want** to see system performance metrics,
**so that** I can monitor system health and performance.

### Story 5.7: Event Detail Modal
**As a** user,
**I want** to click events to see full details,
**so that** I can investigate specific events thoroughly.

### Story 5.8: Search and Filtering
**As a** user,
**I want** to search and filter events by various criteria,
**so that** I can find specific events or patterns.

## Dependencies

- **Epic 3:** Event persistence system must be complete for data access
- **Epic 4:** CLI interface must support `--web` flag for server startup
- **Python Packages:** `fastapi`, `uvicorn`, `python-multipart` (for file uploads)

## Testing Strategy

- **Unit Tests:** API endpoint logic and data transformations
- **Integration Tests:** Full request/response cycles with database
- **E2E Tests:** Browser automation for dashboard interactions
- **Performance Tests:** API response times and dashboard load times
- **Cross-Browser Tests:** Chrome, Safari, Firefox compatibility

## Success Metrics

- **User Satisfaction:** Dashboard enables faster event investigation vs. log files
- **Performance:** <3 second load time, <500ms API responses
- **Reliability:** 99.9% uptime during normal operation
- **Usability:** <5 minutes to learn basic dashboard navigation

## Risk Assessment

**High Risk:**
- Real-time updates complexity (SSE/WebSocket implementation)
- Browser compatibility across different versions
- Performance impact on main processing pipeline

**Medium Risk:**
- CSS layout complexity for responsive design
- API design for efficient data access patterns

**Low Risk:**
- Static file serving
- Basic CRUD operations for events

## Definition of Done

- [ ] All stories implemented and tested
- [ ] Dashboard loads in <3 seconds on target hardware
- [ ] Real-time event updates work reliably
- [ ] Cross-browser compatibility verified
- [ ] API documentation generated (OpenAPI/Swagger)
- [ ] Performance benchmarks meet requirements
- [ ] Code reviewed and merged to main branch
- [ ] Documentation updated in README.md