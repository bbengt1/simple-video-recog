# Ollama LLM Processor

**Responsibility:** Sends annotated images to local Ollama service for semantic description generation using vision-capable LLM (LLaVA or Moondream).

**Key Interfaces:**
- `generate_description(image: np.ndarray, objects: list[DetectedObject]) -> str`: Generate semantic description
- `health_check() -> bool`: Verify Ollama service is available
- `get_available_models() -> list[str]`: List models available in Ollama

**Dependencies:**
- ollama-python client library
- SystemConfig (for ollama_base_url, ollama_model, llm_timeout)

**Technology Stack:**
- Python 3.10+, ollama-python 0.1.0+
- Module path: `integrations/ollama_client.py`
- Class: `OllamaLLMProcessor`

**Implementation Notes:**
- HTTP timeout set to llm_timeout from config (default 10s)
- Prompt template: "Describe what is happening in this image. Focus on: {object_labels}"
- Implements retry with exponential backoff (1 retry, 2s delay) for transient failures
- Falls back to generic description if LLM fails: "Detected: {object_labels}"
- Logs ERROR if Ollama service is unreachable, WARNING if LLM times out

---
