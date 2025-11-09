# User Interface Design Goals

## MVP Scope: CLI Interface

The MVP delivers a **command-line interface only** with no graphical UI. All user interaction occurs through:
- Terminal output (health checks, runtime metrics, event logs)
- Configuration files (YAML editing)
- Command-line flags (--help, --dry-run, --version)
- Signal handling (SIGINT, SIGHUP)

**CLI UX Principles:**
- **Clarity:** All output is human-readable with clear labels and formatting
- **Responsiveness:** Immediate feedback for user actions (startup health check, dry-run validation)
- **Transparency:** Verbose logging options for debugging and learning
- **Professional:** Standard CLI patterns (--help, exit codes, signal handling)

## Phase 2 Vision: Web Dashboard

While not in MVP scope, the following UI/UX vision guides architectural decisions to ensure Phase 2 web dashboard can be built without core refactoring:

### Overall UX Vision

**Primary User Goal:** Monitor video recognition events in real-time with minimal friction, quickly understand what happened and when, and drill into details on demand.

**Design Philosophy:**
- **Dashboard-First:** Single-page application optimized for 4K display on large monitor
- **Real-Time Updates:** Live event feed with WebSocket/SSE for instant notifications
- **Performance-Aware:** Display system health (CPU, memory, inference times) alongside events to support learning goal
- **Privacy-Conscious:** Clean, minimal design with no external CDNs or cloud dependencies (all assets local)

**Key User Flows:**
1. **Monitoring:** Glance at dashboard to see recent events and system health
2. **Investigation:** Click event to see full details (annotated image, JSON metadata, LLM description)
3. **Search:** Filter events by time range, object type, camera (Phase 2 multi-camera)
4. **Configuration:** Adjust thresholds and settings (advanced: hot-reload via UI)

### Key Interaction Paradigms

**Real-Time Event Stream:**
- Auto-scrolling event feed (newest at top)
- Event cards with: timestamp, thumbnail (annotated), semantic description, detected objects
- Click to expand full details
- Pause/resume auto-scroll for investigation

**System Health Monitor:**
- Live metrics dashboard (CPU, memory, inference times, event rate, frame processing time, end-to-end latency)
- System availability indicator (uptime percentage, last 24hr)
- Historical graphs (last 1hr, 24hr, 7 days)
- Status indicators (green/yellow/red) for key thresholds

**Event Detail View:**
- Full-resolution annotated image with bounding boxes
- Complete JSON metadata (formatted, collapsible sections)
- LLM semantic description (highlighted)
- Timeline context (events before/after)
- **Multi-Camera Correlation (Phase 2):** Show related events from other cameras within same time window (e.g., "person detected at front door" correlated with "vehicle detected in driveway")

**Search & Filter:**
- Quick filters: Last hour, Last 24hr, Last 7 days
- Advanced filters: Object type, confidence threshold, camera ID (Phase 2)
- Free-text search of semantic descriptions

### Core Screens and Views

**1. Main Dashboard** (Primary View)
- **Top:** System health bar (CPU, memory, status, uptime)
- **Left Sidebar:** Filters and search
- **Center:** Real-time event feed (scrollable cards)
- **Right Panel:** Selected event details (or collapsed when nothing selected)

**2. Event Detail Modal**
- Full-screen overlay when clicking event
- Large annotated image display
- Tabbed interface: Image | Metadata | Timeline
- Close to return to dashboard

**3. System Metrics Page**
- Performance graphs over time
- Inference speed trends (CoreML, LLM)
- Frame processing time distribution
- End-to-end latency (motion detection → event logged)
- System availability (uptime, downtime events)
- Resource usage history (CPU, memory, disk)
- Event frequency analysis

**4. Settings Page**
- **Web-based YAML Editor:** Editable text area with syntax highlighting for direct YAML editing
- **Form-Based Editor:** Alternative UI with form fields for common parameters (motion threshold, frame sampling rate, logging level)
- **Validation:** Real-time syntax checking and schema validation as user types
- **Apply Changes:** Hot-reload button to apply configuration without restarting system (via SIGHUP)
- **Validation Feedback:** Clear error messages for invalid YAML or out-of-range values
- **Diff View:** Show changes from current configuration before applying
- **Rollback:** Revert to previous configuration if issues occur

**5. Logs Page** (Future)
- Searchable system logs
- Filterable by log level (DEBUG, INFO, WARNING, ERROR)
- Downloadable log exports

### Accessibility

**Target Level:** WCAG AA compliance (Phase 2)

**Authentication:** None required for MVP and Phase 2 - system is local-only on trusted network, accessed via localhost or local IP. Future authentication (Phase 3+) could add HTTP Basic Auth or OIDC if needed.

**Key Considerations:**
- Keyboard navigation throughout (tab order, shortcuts)
- Screen reader support for event descriptions
- High contrast mode option
- Resizable text (respect browser zoom)
- No color-only information (use icons + text labels)

### Branding

**Visual Style:** Minimal, technical, developer-focused

**Aesthetic Inspiration:**
- Terminal/CLI aesthetic (monospace fonts for code/JSON)
- Dark mode by default (optional light mode)
- Syntax highlighting for JSON metadata
- Clean, spacious layout (avoid clutter)

**Color Palette:**
- Background: Dark gray (#1e1e1e) / Light white (#ffffff)
- Primary accent: Blue (#007acc) for interactive elements
- Success: Green (#4caf50) for healthy status
- Warning: Orange (#ff9800) for thresholds approaching
- Error: Red (#f44336) for failures
- Text: Light gray (#d4d4d4) / Dark gray (#333333)

**Typography:**
- Headings: Sans-serif (system font stack: -apple-system, BlinkMacSystemFont, "Segoe UI")
- Body: Sans-serif
- Code/JSON: Monospace (Menlo, Monaco, "Courier New")

### Target Device and Platforms

**Primary:** Web Responsive - Desktop-first, optimized for 4K monitors (3840×2160)

**Supported Browsers:**
- Chrome 100+ (primary development target)
- Safari 15+ (macOS users)
- Firefox 100+ (privacy-conscious users)

**Device Support:**
- Desktop: 27"+ 4K monitor (primary use case)
- Laptop: 13"-16" retina displays (MacBook Pro)
- Tablet: iPad Pro (responsive fallback, limited functionality acceptable)
- Mobile: Not prioritized (monitoring system, not mobile-first)

---
