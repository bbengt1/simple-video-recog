# Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| **Components** | PascalCase | - | `EventCard.js`, `EventTimeline.js` |
| **Hooks/Composables** | camelCase with prefix | - | `useAuth.js`, `useWebSocket.js` |
| **Services** | camelCase | - | `apiClient.js`, `websocketClient.js` |
| **Python Modules** | - | snake_case | `motion_detector.py`, `event_manager.py` |
| **Python Classes** | - | PascalCase | `MotionDetector`, `EventManager` |
| **Python Functions** | - | snake_case | `detect_motion()`, `create_event()` |
| **Python Constants** | - | UPPER_SNAKE_CASE | `MAX_STORAGE_GB`, `DEFAULT_THRESHOLD` |
| **API Routes** | - | kebab-case | `/api/v1/events`, `/api/v1/system-metrics` |
| **Database Tables** | - | snake_case | `events`, `schema_version` |
| **Database Columns** | - | snake_case | `event_id`, `motion_confidence` |
| **Environment Variables** | - | UPPER_SNAKE_CASE | `CAMERA_RTSP_URL`, `OLLAMA_MODEL` |
| **CSS Classes** | BEM: block__element--modifier | - | `.event-card`, `.event-card__image`, `.event-card--highlighted` |
| **Test Files** | `test_*.test.js` | `test_*.py` | `test_event_card.test.js`, `test_event_manager.py` |
| **Configuration Files** | lowercase | lowercase | `config.yaml`, `.env.example` |

**Rationale:**
- Follows community conventions for each language/framework
- PascalCase for classes/components makes them visually distinct
- snake_case for Python aligns with PEP 8
- BEM for CSS prevents naming conflicts in component-heavy UIs

---
