# Epic 5: Web Dashboard - Architecture Diagrams

**Created:** 2025-11-10
**Author:** Winston (Architect)
**Purpose:** Visual architecture reference for Epic 5 implementation

---

## 1. System Overview - Dual Process Architecture

```mermaid
graph TB
    subgraph "User Layer"
        Browser[🌐 Web Browser<br/>Chrome/Safari/Firefox<br/>localhost:8000]
    end

    subgraph "Process 1: Web Server :8000 (NEW - Epic 5)"
        WebServer[FastAPI Application]
        RestAPI[REST API Endpoints<br/>/api/events<br/>/api/metrics<br/>/api/health]
        WSEndpoint[WebSocket Endpoint<br/>/ws/events]
        StaticServer[Static File Server<br/>/images<br/>/]
        DBReader[Database Reader<br/>Read-Only Connection]
    end

    subgraph "Process 2: Video Processing (EXISTING)"
        Pipeline[Processing Pipeline]
        MotionDetect[Motion Detection]
        CoreML[CoreML Inference]
        LLM[Ollama LLM]
        EventMgr[Event Manager]
        DBWriter[Database Writer<br/>Read-Write Connection]
        WSPublisher[WebSocket Publisher<br/>NEW in Epic 5]
    end

    subgraph "Shared Storage Layer"
        DB[(SQLite Database<br/>data/events.db)]
        EventImages[Event Images<br/>data/events/YYYY-MM-DD/]
        MetricsLog[Metrics Log<br/>logs/metrics.json]
    end

    subgraph "External Services (Existing)"
        RTSP[RTSP Camera<br/>rtsp://192.168.1.100]
        Ollama[Ollama Service<br/>localhost:11434]
    end

    Browser -->|HTTP GET /| StaticServer
    Browser -->|HTTP GET /api/events| RestAPI
    Browser -->|HTTP GET /api/metrics| RestAPI
    Browser -->|WS /ws/events| WSEndpoint
    Browser -->|HTTP GET /images/*| StaticServer

    RestAPI --> DBReader
    DBReader -.->|SELECT queries| DB

    StaticServer -.->|Serve files| EventImages

    WSEndpoint <-.->|Subscribe/Broadcast| WSPublisher

    Pipeline --> MotionDetect
    MotionDetect --> CoreML
    CoreML --> LLM
    LLM --> EventMgr
    EventMgr --> DBWriter
    EventMgr --> WSPublisher
    DBWriter -->|INSERT events| DB
    EventMgr -.->|Save images| EventImages
    EventMgr -.->|Log metrics| MetricsLog

    RTSP -->|Video stream| Pipeline
    LLM <-->|HTTP API| Ollama

    style Browser fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    style WebServer fill:#fff4e1,stroke:#f57c00,stroke-width:3px
    style Pipeline fill:#f0f0f0,stroke:#616161,stroke-width:3px
    style DB fill:#ffebee,stroke:#c62828,stroke-width:3px
    style EventImages fill:#ffebee,stroke:#c62828,stroke-width:3px
    style RTSP fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Ollama fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
```

**Key Points:**
- Two independent processes communicating via shared SQLite database and WebSocket
- Web server has read-only database access (prevents write contention)
- Video processing pipeline remains unchanged (sole database writer)
- WebSocket enables real-time event streaming from processing to dashboard

---

## 2. Epic 5 Component Architecture

```mermaid
graph TB
    subgraph "Frontend (Vanilla JavaScript)"
        HTML[index.html<br/>Single Page App]
        AppJS[app.js<br/>Application Bootstrap]
        State[state.js<br/>Observer Pattern]

        subgraph "Components"
            EventFeed[event-feed.js<br/>Live Event Stream]
            EventDetail[event-detail.js<br/>Event Modal]
            MetricsDisplay[metrics.js<br/>System Health]
            SearchFilter[search.js<br/>Event Filtering]
        end

        subgraph "Services"
            APIClient[api-client.js<br/>REST API Wrapper]
            WSClient[websocket-client.js<br/>WebSocket Manager]
        end
    end

    subgraph "Backend (FastAPI)"
        APIApp[api/app.py<br/>FastAPI Application]

        subgraph "Routes"
            EventRoutes[routes/events.py<br/>Event CRUD]
            MetricsRoutes[routes/metrics.py<br/>System Metrics]
            WSRoute[routes/stream.py<br/>WebSocket Handler]
        end

        Dependencies[dependencies.py<br/>DB Session Manager]
        Models[models.py<br/>API Request/Response]
    end

    subgraph "Integration Layer"
        DBManager[core/database.py<br/>DatabaseManager]
        MetricsCollector[core/metrics.py<br/>MetricsCollector]
        EventManager[core/event_manager.py<br/>EventManager + WS]
    end

    HTML --> AppJS
    AppJS --> State
    State --> EventFeed
    State --> EventDetail
    State --> MetricsDisplay
    State --> SearchFilter

    EventFeed --> APIClient
    EventFeed --> WSClient
    MetricsDisplay --> APIClient
    SearchFilter --> APIClient
    EventDetail --> APIClient

    APIClient -->|HTTP| EventRoutes
    APIClient -->|HTTP| MetricsRoutes
    WSClient -->|WebSocket| WSRoute

    EventRoutes --> Dependencies
    MetricsRoutes --> Dependencies
    Dependencies --> DBManager
    Dependencies --> MetricsCollector

    WSRoute <-.-> EventManager

    style HTML fill:#e1f5ff
    style APIApp fill:#fff4e1
    style DBManager fill:#ffebee
```

---

## 3. Real-Time Event Streaming Flow (WebSocket)

```mermaid
sequenceDiagram
    participant Browser as Web Browser
    participant WS as WebSocket Server
    participant EventMgr as Event Manager
    participant Pipeline as Processing Pipeline
    participant DB as SQLite Database

    Note over Browser: User opens dashboard
    Browser->>WS: connect("ws://localhost:8000/ws/events")
    WS-->>Browser: Connection accepted
    WS->>WS: Add client to subscribers list

    Note over Browser: Connection established<br/>Waiting for events...

    Note over Pipeline: Camera detects motion
    Pipeline->>Pipeline: Capture frame
    Pipeline->>Pipeline: Run CoreML + LLM
    Pipeline->>EventMgr: create_event(frame, objects, description)

    EventMgr->>DB: INSERT INTO events (...)
    DB-->>EventMgr: Success

    EventMgr->>EventMgr: Save annotated image

    Note over EventMgr: NEW: Broadcast to WebSocket
    EventMgr->>WS: broadcast_event(event)

    WS->>WS: Serialize event to JSON
    WS->>Browser: WebSocket message<br/>{"type": "event", "data": {...}}

    Note over Browser: Update UI in real-time
    Browser->>Browser: Display notification
    Browser->>Browser: Prepend to event feed
    Browser->>Browser: Update event counter

    Note over Browser: User navigates away
    Browser->>WS: close()
    WS->>WS: Remove client from subscribers
```

---

## 4. API Request/Response Flow

```mermaid
sequenceDiagram
    participant Browser as Web Browser
    participant FastAPI as FastAPI Server
    participant DBReader as DB Reader (Read-Only)
    participant DB as SQLite Database
    participant FileSystem as Event Images

    Note over Browser: User loads dashboard
    Browser->>FastAPI: GET /api/events?limit=100
    FastAPI->>DBReader: get_recent_events(limit=100)
    DBReader->>DB: SELECT * FROM events<br/>ORDER BY timestamp DESC<br/>LIMIT 100
    DB-->>DBReader: [event1, event2, ..., event100]
    DBReader-->>FastAPI: List[Event]
    FastAPI-->>Browser: 200 OK<br/>{"events": [...], "total": 100}

    Note over Browser: Render event feed

    Note over Browser: User clicks event
    Browser->>FastAPI: GET /api/events/evt_12345_abc
    FastAPI->>DBReader: get_event_by_id("evt_12345_abc")
    DBReader->>DB: SELECT * FROM events<br/>WHERE event_id = ?
    DB-->>DBReader: Event object
    DBReader-->>FastAPI: Event
    FastAPI-->>Browser: 200 OK<br/>{"event_id": "evt_12345_abc", ...}

    Note over Browser: Display event details modal

    Browser->>FastAPI: GET /images/2025-11-10/evt_12345_abc.jpg
    FastAPI->>FileSystem: Read image file
    FileSystem-->>FastAPI: Image bytes
    FastAPI-->>Browser: 200 OK<br/>image/jpeg

    Note over Browser: Display annotated image
```

---

## 5. Frontend State Management (Observer Pattern)

```mermaid
graph TB
    subgraph "AppState (Custom Observer)"
        State[AppState Instance<br/>Singleton]
        Events[events: Array]
        Metrics[metrics: Object]
        Filters[filters: Object]
        Listeners[listeners: Map]
    end

    subgraph "Components (Subscribers)"
        EventFeed[EventFeed Component]
        EventDetail[EventDetail Component]
        MetricsDisplay[MetricsDisplay Component]
        SearchFilter[SearchFilter Component]
    end

    subgraph "Data Sources (Publishers)"
        WSClient[WebSocket Client]
        APIClient[API Client]
        UserInput[User Interactions]
    end

    WSClient -->|"state.set('events', newEvents)"| State
    APIClient -->|"state.set('metrics', data)"| State
    UserInput -->|"state.set('filters', {...})"| State

    State -->|"notify('events', data)"| Listeners
    State -->|"notify('metrics', data)"| Listeners
    State -->|"notify('filters', data)"| Listeners

    Listeners -->|"callback(newEvents)"| EventFeed
    Listeners -->|"callback(metrics)"| MetricsDisplay
    Listeners -->|"callback(filters)"| SearchFilter
    Listeners -->|"callback(event)"| EventDetail

    EventFeed -->|"state.subscribe('events', cb)"| State
    MetricsDisplay -->|"state.subscribe('metrics', cb)"| State
    SearchFilter -->|"state.subscribe('filters', cb)"| State
    EventDetail -->|"state.subscribe('selectedEvent', cb)"| State

    style State fill:#fff4e1,stroke:#f57c00,stroke-width:3px
    style WSClient fill:#e8f5e9
    style APIClient fill:#e8f5e9
```

**Code Example:**
```javascript
// state.js - Custom Observer Pattern
class AppState {
    constructor() {
        this.events = [];
        this.metrics = {};
        this.filters = {};
        this.listeners = new Map();
    }

    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);
    }

    set(key, value) {
        this[key] = value;
        this.notify(key, value);
    }

    notify(key, value) {
        if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(cb => cb(value));
        }
    }
}

export const appState = new AppState();
```

---

## 6. Database Schema (Epic 5 Enhancements)

```mermaid
erDiagram
    EVENTS {
        string event_id PK "evt_1699459335_a7b3c"
        datetime timestamp "Indexed DESC"
        string camera_id "Indexed"
        float motion_confidence
        json detected_objects
        string llm_description
        string image_path
        string json_log_path
        datetime created_at
    }

    DETECTED_OBJECTS {
        string label
        float confidence
        json bbox
    }

    SCHEMA_VERSION {
        int version "Current: 3"
        datetime updated_at
    }

    INDEXES {
        string idx_events_timestamp "timestamp DESC"
        string idx_events_camera "camera_id"
        string idx_events_timestamp_camera "timestamp, camera_id"
        string idx_events_event_id "event_id"
    }

    EVENTS ||--o{ DETECTED_OBJECTS : contains
    EVENTS ||--|| SCHEMA_VERSION : tracks
    EVENTS ||--o{ INDEXES : optimizes
```

**Migration 003 (Epic 5):**
```sql
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_camera ON events(camera_id);
CREATE INDEX idx_events_timestamp_camera ON events(timestamp DESC, camera_id);
CREATE INDEX idx_events_event_id ON events(event_id);
```

**Query Performance Impact:**
- Recent events query: ~10x faster (1000ms → 100ms for 10K events)
- Time-range queries: ~5x faster (500ms → 100ms)
- Camera filtering: ~8x faster (800ms → 100ms)

---

## 7. WebSocket Connection Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Disconnected

    Disconnected --> Connecting: User opens dashboard
    Connecting --> Connected: Connection accepted
    Connecting --> ConnectionFailed: Network error

    Connected --> Receiving: Event broadcast
    Receiving --> Connected: Message processed

    Connected --> Reconnecting: Connection lost
    ConnectionFailed --> Reconnecting: Retry with backoff

    Reconnecting --> Connected: Reconnection successful
    Reconnecting --> Disconnected: Max retries exceeded

    Connected --> Disconnected: User closes dashboard

    note right of Reconnecting
        Exponential backoff:
        1s → 2s → 4s → 8s
    end note

    note right of Connected
        Heartbeat every 30s
        to detect stale connections
    end note
```

**WebSocket Client Logic:**
```javascript
// websocket-client.js
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectDelay = 1000; // Start at 1s
        this.maxReconnectDelay = 8000; // Max 8s
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectDelay = 1000; // Reset on success
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'event') {
                appState.set('newEvent', message.data);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed, reconnecting...');
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(
                this.reconnectDelay * 2,
                this.maxReconnectDelay
            );
        };
    }
}
```

---

## 8. API Endpoint Structure

```mermaid
graph LR
    subgraph "API Routes :8000"
        Root[/ Root<br/>Serve index.html]

        subgraph "REST API /api"
            Health[/api/health<br/>GET Health Check]
            Metrics[/api/metrics<br/>GET Current Metrics]
            Events[/api/events<br/>GET List Events]
            EventByID[/api/events/:id<br/>GET Event Details]
            EventImage[/api/events/:id/image<br/>GET Annotated Image]
            Config[/api/config<br/>GET System Config]
        end

        subgraph "WebSocket"
            WSEvents[/ws/events<br/>WebSocket Stream]
        end

        subgraph "Static Files"
            Images[/images/*<br/>Serve Event Images]
            CSS[/css/*<br/>Serve Stylesheets]
            JS[/js/*<br/>Serve JavaScript]
        end
    end

    style Health fill:#c8e6c9
    style Metrics fill:#c8e6c9
    style Events fill:#c8e6c9
    style EventByID fill:#c8e6c9
    style EventImage fill:#c8e6c9
    style Config fill:#c8e6c9
    style WSEvents fill:#fff9c4
    style Images fill:#e1f5fe
    style CSS fill:#e1f5fe
    style JS fill:#e1f5fe
```

**API Endpoints Summary:**

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/api/health` | GET | Service health status | <50ms |
| `/api/metrics` | GET | Current system metrics | <100ms |
| `/api/events` | GET | List events (paginated) | <500ms |
| `/api/events/:id` | GET | Get single event | <100ms |
| `/api/events/:id/image` | GET | Get annotated image | <200ms |
| `/api/config` | GET | System configuration | <50ms |
| `/ws/events` | WS | Real-time event stream | <1s latency |

---

## 9. Directory Structure (Epic 5 Additions)

```
video-recognition/
├── api/                          # NEW: FastAPI web server
│   ├── __init__.py
│   ├── app.py                    # FastAPI application factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── events.py             # Event CRUD endpoints
│   │   ├── metrics.py            # System metrics endpoint
│   │   └── stream.py             # WebSocket endpoint
│   ├── dependencies.py           # DB session, metrics injection
│   └── models.py                 # API request/response models
│
├── web/                          # NEW: Frontend assets
│   ├── index.html                # Main dashboard page
│   ├── css/
│   │   ├── main.css              # Core styles
│   │   ├── components.css        # Component styles
│   │   └── layout.css            # Grid/Flexbox layout
│   └── js/
│       ├── app.js                # Application bootstrap
│       ├── state.js              # Observer pattern state
│       ├── components/
│       │   ├── event-feed.js     # Live event stream component
│       │   ├── event-detail.js   # Event detail modal
│       │   ├── metrics.js        # System health display
│       │   └── search.js         # Search and filtering
│       └── services/
│           ├── api-client.js     # REST API wrapper
│           └── websocket-client.js  # WebSocket manager
│
├── web_server.py                 # NEW: Web server entry point
│
├── migrations/
│   └── 003_add_api_indexes.sql   # NEW: API query optimization
│
├── core/                         # EXISTING (minor updates)
│   ├── event_manager.py          # UPDATED: Add WebSocket publisher
│   └── ...
│
└── tests/
    ├── api/                      # NEW: API endpoint tests
    │   ├── test_events_api.py
    │   ├── test_metrics_api.py
    │   └── test_websocket.py
    └── integration/              # NEW: Full-stack tests
        └── test_dashboard_e2e.py
```

---

## 10. Performance Optimization Strategy

```mermaid
graph TB
    subgraph "Frontend Optimizations"
        LazyLoad[Lazy Load Images<br/>Only visible events]
        Debounce[Debounce Search<br/>300ms delay]
        VirtualScroll[Virtual Scrolling<br/>Max 100 visible]
        CacheBust[Cache Busting<br/>Version in URL]
    end

    subgraph "Backend Optimizations"
        DBIndex[Database Indexes<br/>timestamp, camera_id]
        ReadOnly[Read-Only Connection<br/>No write locks]
        Pagination[Pagination<br/>Limit 100 events]
        Compression[Gzip Compression<br/>Static assets]
    end

    subgraph "Network Optimizations"
        WSCompression[WebSocket Compression<br/>Per-message deflate]
        HTTPCache[HTTP Cache Headers<br/>images: 7 days]
        MinifyCSS[Minify CSS/JS<br/>Production build]
    end

    Browser[Web Browser] --> LazyLoad
    Browser --> Debounce
    LazyLoad --> VirtualScroll

    VirtualScroll -->|HTTP| Pagination
    Debounce -->|HTTP| DBIndex

    DBIndex --> ReadOnly
    Pagination --> ReadOnly

    WSCompression --> Browser
    HTTPCache --> Browser
    MinifyCSS --> Browser

    style Browser fill:#e1f5ff
    style DBIndex fill:#fff4e1
    style ReadOnly fill:#fff4e1
```

**Performance Targets vs Optimizations:**

| Target | Without Optimization | With Optimization | Strategy |
|--------|---------------------|-------------------|----------|
| Dashboard load <3s | ~8s (no minification) | ~1.5s | Minify CSS/JS, gzip |
| API response <500ms | ~2s (no indexes) | ~100ms | Database indexes |
| WebSocket latency <1s | ~1s (baseline) | ~200ms | Direct EventManager integration |
| Memory <200MB | ~300MB (all events) | ~150MB | Limit to 100 events, lazy load |

---

## 11. Error Handling and Fallback Strategy

```mermaid
graph TB
    subgraph "Primary Path"
        WS[WebSocket Connection]
        LiveFeed[Live Event Feed]
    end

    subgraph "Fallback Path"
        WSFailed{WebSocket Failed?}
        Polling[REST API Polling<br/>every 5 seconds]
        EventList[Event List<br/>No live updates]
    end

    subgraph "Recovery"
        Reconnect[Exponential Backoff<br/>Reconnection]
        MaxRetries{Max Retries?}
        UserNotify[User Notification<br/>"Connection lost"]
    end

    WS --> LiveFeed
    WS -.->|Connection Error| WSFailed

    WSFailed -->|Yes| Reconnect
    Reconnect --> MaxRetries
    MaxRetries -->|Exceeded| Polling
    MaxRetries -->|Continue| WS

    Polling --> EventList
    Polling --> UserNotify

    Reconnect -.->|Success| WS

    style WS fill:#c8e6c9
    style LiveFeed fill:#c8e6c9
    style Polling fill:#fff9c4
    style EventList fill:#fff9c4
    style UserNotify fill:#ffccbc
```

**Error Scenarios:**

| Error | Detection | Recovery | User Impact |
|-------|-----------|----------|-------------|
| WebSocket connection failed | `onerror` event | Exponential backoff reconnect | ⚠️ Warning banner, fallback to polling |
| API endpoint timeout (>2s) | Fetch timeout | Retry once, then error | ❌ Error message, retry button |
| Database read error | API 500 response | Log error, return empty array | ⚠️ "No events found" message |
| Image load failed | 404 response | Show placeholder image | ℹ️ Placeholder with retry icon |

---

## 12. Deployment Architecture (Phase 2)

```mermaid
graph TB
    subgraph "Mac Mini / Mac Studio"
        subgraph "Process 1: Video Processing"
            Main[python main.py]
            RTSP[RTSP Connection]
            Processing[Frame Processing]
            Database[SQLite Write]
        end

        subgraph "Process 2: Web Server"
            WebServer[python web_server.py<br/>:8000]
            FastAPI[FastAPI + Uvicorn]
            DBRead[SQLite Read-Only]
        end

        subgraph "Storage"
            DBFile[data/events.db]
            Images[data/events/*/]
        end
    end

    subgraph "User Device"
        Browser[Web Browser<br/>http://localhost:8000]
    end

    Main --> Processing
    Processing --> Database
    Database --> DBFile

    WebServer --> FastAPI
    FastAPI --> DBRead
    DBRead -.-> DBFile
    FastAPI -.-> Images

    Browser -->|HTTP/WS| FastAPI

    style Main fill:#f0f0f0
    style WebServer fill:#fff4e1
    style Browser fill:#e1f5ff
    style DBFile fill:#ffebee
```

**Startup Process:**

```bash
# Terminal 1: Start video processing
cd /path/to/video-recognition
source venv/bin/activate
python main.py

# Terminal 2: Start web server
cd /path/to/video-recognition
source venv/bin/activate
python web_server.py

# Open browser
# http://localhost:8000
```

**Future Enhancement (Epic 6):**
```bash
# Single command startup with subprocess management
python main.py --web
# Spawns web_server.py as subprocess
# Monitors both processes
# Graceful shutdown of both on Ctrl+C
```

---

## Summary

**Epic 5 Architecture Characteristics:**

✅ **Separation of Concerns**
- Video processing and web serving in separate processes
- Read-only database access for API (no write contention)
- Static frontend assets (no build step required)

✅ **Real-Time Communication**
- WebSocket for live event streaming
- Exponential backoff reconnection
- Fallback to REST API polling

✅ **Performance Optimized**
- Database indexes for <500ms queries
- Lazy loading for images
- Virtual scrolling for long event lists

✅ **Fault Tolerant**
- Process isolation (web crash doesn't affect video processing)
- Graceful degradation (WebSocket → polling)
- User-friendly error messages

✅ **Developer Friendly**
- Zero build step (vanilla JavaScript)
- Auto-generated API docs (FastAPI/OpenAPI)
- Clear component boundaries

**Next Steps:**
1. Review diagrams for accuracy
2. Begin Story 5.1 implementation (FastAPI server setup)
3. Reference diagrams during development

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-10 | 1.0 | Initial architecture diagrams for Epic 5 | Winston (Architect) |

