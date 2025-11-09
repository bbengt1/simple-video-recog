# Test Organization

## Frontend Tests (Phase 2)

```
tests/frontend/
├── unit/
│   ├── test_state_manager.test.js       # State management logic
│   ├── test_api_client.test.js          # API client wrapper
│   ├── test_websocket_client.test.js    # WebSocket reconnection
│   └── test_date_formatter.test.js      # Utility functions
├── integration/
│   ├── test_component_rendering.test.js # Component DOM tests
│   └── test_api_integration.test.js     # Real API calls
└── e2e/
    ├── test_dashboard_workflow.spec.js  # Full user journey
    └── test_event_timeline.spec.js      # Timeline interactions
```

**Frontend Testing Tools (Phase 2):**
- Unit: Vitest or Jest (JavaScript testing framework)
- DOM testing: @testing-library/dom (vanilla JS component testing)
- E2E: Playwright (Phase 3)
- Coverage: c8 or Istanbul

**Not Implemented in Phase 1:**
- Frontend tests deferred to Phase 2 (no web UI in Phase 1)
- Manual testing of web dashboard sufficient for personal project

---

## Backend Tests

```
tests/
├── unit/
│   ├── test_motion_detector.py          # Motion detection algorithm
│   ├── test_event_manager.py            # Event creation and de-duplication
│   ├── test_database.py                 # DatabaseManager (mocked SQLite)
│   ├── test_storage_monitor.py          # Storage calculations
│   ├── test_log_rotation.py             # FIFO deletion logic
│   ├── test_metrics.py                  # Metrics collection
│   ├── test_json_logger.py              # JSON log writing
│   ├── test_plaintext_logger.py         # Plaintext log writing
│   └── test_config.py                   # Pydantic config validation
│
├── integration/
│   ├── test_database_integration.py     # Real SQLite operations
│   ├── test_rtsp_integration.py         # RTSP connection (mock camera)
│   ├── test_ollama_integration.py       # Ollama service calls
│   ├── test_pipeline_integration.py     # Full pipeline with test data
│   ├── test_api_integration.py          # FastAPI endpoints (Phase 2)
│   └── test_websocket_integration.py    # WebSocket streaming (Phase 2)
│
└── performance/
    ├── test_coreml_performance.py       # CoreML <100ms validation
    ├── test_llm_performance.py          # Ollama <3s validation
    ├── test_pipeline_throughput.py      # Events/minute throughput
    └── test_storage_growth.py           # Storage limit enforcement
```

**Backend Testing Tools:**
- Test framework: pytest 7.4+
- Coverage: pytest-cov (target ≥70%)
- Mocking: pytest-mock, unittest.mock
- Fixtures: pytest fixtures for common test data
- Performance: pytest-benchmark (for performance tests)

---
