# Integration Test Strategy

**Database Integration Tests:**
- Use real SQLite database in temp directory
- Test schema creation, migrations, CRUD operations
- Verify indexes are created correctly
- Test concurrent reads (multiple queries simultaneously)

**RTSP Integration Tests:**
- Mock RTSP camera using test video file
- Test connection establishment and reconnection logic
- Validate frame capture and timeout handling
- Skip if no test camera available (pytest.mark.skipif)

**Ollama Integration Tests:**
- Require Ollama service running locally
- Use smaller model (moondream) for faster tests
- Test health check, model availability, inference
- Skip if Ollama not available (pytest.mark.skipif)

**Pipeline Integration Tests:**
- Use test video file instead of live camera
- Mock CoreML with fast detector (returns predefined objects)
- Use real database, loggers, storage monitor
- Verify events created and persisted correctly

---
