# Testing Pyramid

```
                    E2E Tests (5%)
                   /            \
                  /   Manual     \
                 /   Exploratory  \
                /                  \
           Integration Tests (25%)
          /                        \
         /    API Tests              \
        /    Database Tests           \
       /     Pipeline Tests            \
      /                                \
 Unit Tests (70%)
/    Core Logic                        \
     Platform Code
     Integrations
     Mocking External Dependencies
```

**Testing Distribution:**
- **Unit Tests (70%):** Fast, isolated tests with mocked dependencies
- **Integration Tests (25%):** Tests with real dependencies (database, file system, external services)
- **E2E Tests (5%):** Full workflow validation (Phase 3, manual for Phase 1/2)

**Rationale:**
- Heavy unit test coverage provides fast feedback loop (<10s execution)
- Integration tests validate component interactions without mocking
- E2E tests deferred to Phase 3 (manual testing sufficient for MVP)
- 70% unit test coverage meets ≥70% code coverage NFR requirement

---
