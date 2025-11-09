# 3. Graceful Shutdown (SIGINT/SIGTERM Handling)

```mermaid
sequenceDiagram
    participant OS as Operating System
    participant Main as main.py
    participant Pipeline as Processing Pipeline
    participant RTSP as RTSP Client
    participant DB as Database Manager
    participant Loggers as JSON/Plaintext Loggers

    OS->>Main: SIGINT (Ctrl+C)

    Main->>Pipeline: shutdown()
    Pipeline->>Pipeline: set shutdown_event

    Note over Pipeline: Complete current frame processing

    Pipeline->>RTSP: disconnect()
    RTSP-->>Pipeline: void

    Pipeline->>DB: close_connection()
    DB-->>Pipeline: void

    Pipeline->>Loggers: flush_buffers()
    Loggers-->>Pipeline: void

    Pipeline-->>Main: shutdown complete

    Main->>Main: log("System shutdown gracefully")
    Main->>OS: exit(0)
```

**Signal Handling:**
- SIGINT (Ctrl+C): Graceful shutdown, logs "User interrupted"
- SIGTERM: Graceful shutdown, logs "Termination signal received"
- SIGHUP (Phase 2): Hot-reload configuration without restart

---
