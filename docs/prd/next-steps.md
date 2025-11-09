# Next Steps

## UX Expert Prompt

**Note:** UX work is planned for Phase 2 (Web Dashboard). For Phase 1 MVP, CLI interface is well-specified in Epic 4. When ready for Phase 2:

```
Create web dashboard UI specification for Local Video Recognition System based on PRD docs/prd.md.

Focus on:
- 5 core screens: Dashboard, Event Timeline, Event Detail, Settings, System Status
- Multi-camera event correlation visualization
- Web-based YAML configuration editor with validation
- Performance metrics display (frame processing time, latency, availability)
- Dark mode optimized for 4K desktop displays
- No authentication (local-only access)

Reference PRD Section "User Interface Design Goals" for detailed requirements.
```

## Architect Prompt

```
Create technical architecture document for Local Video Recognition System based on PRD docs/prd.md.

Key areas for architectural investigation:
1. CoreML model selection (YOLO vs MobileNet vs others) - optimize for Apple Neural Engine <100ms inference
2. Concurrency strategy (threading vs asyncio) for processing pipeline (motion detection → CoreML → Ollama → persistence)
3. Ollama model benchmarking (LLaVA vs Moondream) - balance speed vs accuracy for semantic descriptions
4. SQLite connection management for concurrent writes (event persistence during high-frequency motion events)
5. Schema versioning and migration strategy for database evolution

Technical constraints are documented in PRD Section "Technical Assumptions". All technology choices are already defined (Python 3.10+, SQLite, FastAPI, OpenCV, etc.).

Focus on:
- Processing pipeline architecture (stages, data flow, error handling)
- Module structure following monorepo layout (core/, platform/, integrations/)
- Class hierarchy and interfaces for extensibility
- Performance optimization strategies to meet NFR targets
- Testing architecture to achieve ≥70% coverage

Deliverable: docs/architecture.md following architecture template.
```

---
