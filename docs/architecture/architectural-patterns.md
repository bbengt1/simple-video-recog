# Architectural Patterns

- **Pipeline Pattern:** Sequential frame processing through motion detection → CoreML → LLM → persistence stages. Each stage has clear inputs/outputs and can be tested independently. _Rationale:_ Simplifies error handling and makes performance bottlenecks easy to identify. Sequential execution matches the natural flow of video frame processing.

- **Repository Pattern:** DatabaseManager abstracts all SQLite operations behind a clean interface (insert_event, get_events_by_timerange, etc.). _Rationale:_ Isolates database implementation details, enables easy mocking for tests, and provides a single point of control for data access.

- **Dependency Injection:** Components receive dependencies through constructor parameters rather than creating them internally. Example: ProcessingPipeline receives motion_detector, object_detector, llm_processor instances. _Rationale:_ Enables unit testing with mock objects and makes component dependencies explicit.

- **Event-Driven Architecture (Phase 2):** WebSocket server publishes new events to connected clients in real-time. _Rationale:_ Decouples event creation from event delivery, allowing multiple clients to receive updates without polling.

- **Observer Pattern (Frontend State Management):** Custom state management where UI components subscribe to state changes. _Rationale:_ Avoids framework overhead while providing reactive UI updates. Lightweight alternative to Redux/MobX for simple state.

- **Monolith → Modular Monolith Evolution:** Phase 1 is a single-process CLI application. Phase 2 separates into two processes (processing engine + API server) sharing the same database. _Rationale:_ Maintains simplicity for MVP while enabling web access in Phase 2. Avoids premature microservices complexity.

---
