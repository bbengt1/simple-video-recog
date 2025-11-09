# Monitoring Stack

**Frontend Monitoring (Phase 2):**
- **Tool:** Browser DevTools + Console Logging
- **Metrics Collected:** Page load time, API response times, JavaScript errors
- **Implementation:** Custom performance marks and console error tracking
- **Phase 3 Enhancement:** Consider Sentry or LogRocket for production error tracking

**Backend Monitoring:**
- **Tool:** Custom metrics collection to `logs/metrics.json`
- **Metrics Collected:** Frame processing rate, inference times, CPU/memory usage, event counts
- **Implementation:** MetricsCollector class with 60-second sampling interval
- **Storage:** JSON Lines format in `logs/metrics.json` (enables easy parsing and analysis)

**Error Tracking:**
- **Tool:** Python logging module with structured logging
- **Storage:** `logs/app.log` (rotating file handler, max 100MB, 5 backups)
- **Log Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Structured Data:** Extra fields via `logger.info(..., extra={...})`
- **Phase 3 Enhancement:** Consider centralized logging with Loki or ELK stack

**Performance Monitoring:**
- **Tool:** Custom timing instrumentation in processing pipeline
- **Metrics Tracked:** CoreML inference time (p50, p95, p99), LLM inference time, end-to-end latency
- **Validation:** Performance tests in `tests/performance/` validate NFR targets
- **Alerting:** Log WARNING if metrics exceed thresholds (CoreML >100ms, LLM >3s)

**System Resource Monitoring:**
- **Tool:** psutil library for CPU/memory monitoring
- **Metrics:** CPU usage (%), memory usage (MB), disk usage (GB)
- **Frequency:** Collected every 60 seconds, logged to metrics.json
- **Alerts:** Storage >80% logs WARNING, >100% triggers graceful shutdown

**Rationale:**
- Simple, file-based monitoring sufficient for Phase 1/2 (single user, local deployment)
- No external monitoring service needed (privacy-first, no cloud dependencies)
- JSON Lines format enables easy analysis with standard tools (jq, Python, spreadsheets)
- Phase 3 can add Prometheus + Grafana if needed for advanced dashboards

---
