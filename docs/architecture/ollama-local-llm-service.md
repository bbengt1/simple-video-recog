# Ollama Local LLM Service

- **Purpose:** Local LLM inference for generating semantic descriptions of detected events
- **Documentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Base URL(s):** http://localhost:11434 (default), configurable via SystemConfig
- **Authentication:** None (local service, no auth required)
- **Rate Limits:** None (local service, limited only by hardware)

**Key Endpoints Used:**
- `POST /api/generate` - Generate text completion with vision model
- `GET /api/tags` - List available models (for health check)

**Integration Notes:**
- Requires Ollama service running locally before application startup
- Recommended models: llava:7b (better accuracy) or moondream:latest (faster inference)
- Health check validates Ollama is reachable and model is downloaded
- Timeout: 10 seconds (configurable via llm_timeout)
- Error handling: Falls back to generic description if LLM unavailable
- Vision models accept image + text prompt, return natural language description

**Installation:**
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Download vision model
ollama pull llava:7b
```

---
