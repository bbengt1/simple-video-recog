# WebSocket Server (Phase 2)

**Responsibility:** Broadcasts new events to connected web dashboard clients in real-time via WebSocket protocol.

**Key Interfaces:**
- WebSocket endpoint: `/ws/events`
- Connection manager tracks active clients
- Broadcast method sends events to all subscribers

**Dependencies:**
- FastAPI WebSocket support
- Event serialization (Pydantic model)

**Technology Stack:**
- Python 3.10+, FastAPI WebSocket, websockets library
- Module path: `api/websocket.py`
- Class: `WebSocketManager`

**Implementation Notes:**
- Integrated with EventManager to receive new events
- Maintains list of active WebSocket connections
- Broadcasts to all clients when new event created
- Removes disconnected clients from subscriber list
- No authentication in Phase 2

---
