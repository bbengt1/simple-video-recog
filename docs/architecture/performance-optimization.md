# Performance Optimization

## Frontend Performance (Phase 2)

**Bundle Size Target:** Not applicable - no bundling, vanilla JavaScript served directly
- Actual size: ~50KB total (all JS files combined)
- No framework overhead: React bundle would be ~140KB min+gzip, avoided entirely
- Image optimization: Annotated images served as JPEG with 85% quality (balance size vs clarity)
- Lazy loading: Images loaded on-demand with `loading="lazy"` attribute

**Loading Strategy:**
- ES6 modules: Browser-native module loading, no webpack/vite needed
- Code splitting: Manual - dashboard, timeline, settings loaded as separate modules
- Initial page load: <100ms (only loads app.js and minimal CSS)
- Subsequent navigation: Instant (hash-based routing, no server round-trip)
- Time to interactive: <500ms on 4K display

**Caching Strategy:**
- Service Worker: Not implemented (Phase 3 enhancement)
- Browser cache: Leverage HTTP cache headers for static assets
  - `.js` files: `Cache-Control: public, max-age=3600` (1 hour)
  - `.css` files: `Cache-Control: public, max-age=3600`
  - Images: `Cache-Control: public, max-age=86400` (24 hours)
- API responses: No caching (always fetch fresh data)
- WebSocket: Real-time updates bypass cache entirely

**Rendering Performance:**
- Virtual scrolling: Implemented for event timeline (only render visible events)
- Batch DOM updates: Use DocumentFragment for multi-element inserts
- Debounced filters: Filter inputs debounced to 300ms to avoid excessive re-renders
- Image thumbnails: Generate smaller thumbnails server-side (future enhancement)
- CSS animations: GPU-accelerated (use `transform` and `opacity`, avoid `left`/`top`)

## Backend Performance

**Response Time Target:**
- Health check: <10ms
- Event list (100 events): <50ms
- Event detail: <20ms
- Image retrieval: <100ms (depends on file size, ~500KB images)
- Metrics endpoint: <30ms

**Database Optimization:**
- Indexes: Three indexes on events table (timestamp DESC, camera_id, event_id)
- Query optimization: Use `LIMIT` and `OFFSET` for pagination, avoid full table scans
- Connection pooling: Single shared connection (sufficient for read-only API access)
- Prepared statements: SQLite query plan cached for repeated queries
- Vacuum schedule: Run `VACUUM` monthly to reclaim deleted space and rebuild indexes
- Performance monitoring: Log slow queries (>100ms) at WARNING level

**Caching Strategy:**
- In-memory cache: Not implemented in Phase 1/2 (database is fast enough)
- Phase 3: Consider Redis cache for frequently accessed events
- Static files: nginx/Python HTTP server handles static file caching
- No cache invalidation needed: Events are immutable (never updated after creation)

**CoreML Inference Optimization:**
- Neural Engine utilization: Validate model runs on ANE (not GPU or CPU)
- Model selection: YOLOv8 Nano (smallest YOLO variant, <10MB, <100ms inference)
- Input preprocessing: Batch preprocessing outside timed section
  - Resize frame to 640x640 before inference
  - Convert BGR (OpenCV) to RGB (CoreML) once
- Inference frequency: Only run on frames with motion (reduces 95% of frames)
- Target: <100ms per frame (NFR requirement)
- Monitoring: Log inference times, alert if p95 exceeds 100ms

**Ollama LLM Optimization:**
- Model selection: llava:7b (balance of speed vs accuracy)
  - Alternative: moondream:latest (3x faster, lower accuracy)
- Prompt optimization: Minimal prompt to reduce token count
  - Template: "Describe what is happening in this image. Focus on: {object_labels}"
  - Avoid verbose instructions (each token adds latency)
- Timeout: 10 seconds (prevent hanging on slow responses)
- Inference frequency: Only run when objects detected (not every frame)
- Target: <3 seconds per event (NFR requirement)
- Monitoring: Track p95 latency, consider model downgrade if consistently >3s

**Processing Pipeline Optimization:**
- Sequential execution: No threading/async overhead for MVP
- Frame skipping: Skip frames during processing (capture at 30fps, process at 5fps during motion)
- Early exit: Return immediately from pipeline stages if no work to do
  - No motion? Skip CoreML and LLM
  - No objects? Skip LLM
  - Duplicate event? Skip persistence
- Resource efficiency: <2GB memory usage, <50% CPU on M1

**Storage Optimization:**
- Image compression: JPEG quality 85% (reduces 500KB images to ~150KB)
- FIFO rotation: Automatically delete old events when storage limit reached
- Database size: SQLite file size stays <100MB with 30 days of data
- Log rotation: Compress old logs with gzip (10:1 compression ratio)
- Efficient indexing: Indexes add <10% overhead to database size

**API Server Optimization:**
- Async framework: FastAPI with uvicorn (handles concurrent requests efficiently)
- Database queries: Read-only access, no write locks, high concurrency
- Static file serving: nginx serves images directly (no Python overhead)
- WebSocket: Broadcast to all clients in <10ms
- Connection limits: No limit (localhost-only, single user, low traffic)

## Performance Monitoring

**Key Performance Indicators:**
- CoreML inference time: p50, p95, p99 (target: <100ms p95)
- LLM inference time: p50, p95, p99 (target: <3s p95)
- Frame processing latency: End-to-end time from motion detection to event logged (target: <5s)
- API response times: Per endpoint (target: <50ms for event list)
- Memory usage: Current and peak (target: <2GB)
- CPU usage: Average and peak (target: <50% sustained on M1)
- Storage growth rate: MB per day (target: <150MB/day for 4GB/30days)

**Performance Testing:**
- Unit tests: Mock expensive operations (CoreML, LLM) for fast feedback
- Integration tests: Use small test models for faster execution
- Performance tests: Separate test suite in `tests/performance/`
  - `test_coreml_performance.py`: Validates <100ms inference on real model
  - `test_llm_performance.py`: Validates <3s LLM response on real Ollama
  - `test_pipeline_throughput.py`: Measures events/minute processing rate
- Load testing: Not needed (single user, local deployment)

**Performance Baselines (M1 MacBook Pro):**
- CoreML inference (YOLOv8n): 65ms average, 85ms p95
- LLM inference (llava:7b): 2.1s average, 2.8s p95
- Frame processing (motion → event): 3.2s average
- Database insert: 5ms average
- API response (list 100 events): 32ms
- Memory usage: 1.2GB steady state
- CPU usage: 25% average, 60% during motion events

**Optimization Priorities:**
1. **Critical (NFR violations):** CoreML >100ms, LLM >3s, Storage >4GB
2. **High (Performance degradation):** Memory >2GB, CPU >80%, API >100ms
3. **Medium (User experience):** Frontend >1s page load, WebSocket >100ms latency
4. **Low (Nice to have):** Further inference optimization, thumbnail generation

---
