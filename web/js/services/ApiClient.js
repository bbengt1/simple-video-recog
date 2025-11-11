// ApiClient - REST API client for dashboard
// Handles HTTP requests to the FastAPI backend

class ApiClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async getEvents(params = {}) {
    const {
      limit = 100,
      offset = 0,
      start = null,
      end = null,
      camera_id = null
    } = params;

    // Build query string
    const query = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });

    if (start) query.append('start', start);
    if (end) query.append('end', end);
    if (camera_id) query.append('camera_id', camera_id);

    const url = `${this.baseUrl}/api/events?${query}`;

    console.log(`[API] GET ${url}`);

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('[API] Request failed:', error);
      throw error;
    }
  }

  getImageUrl(eventId) {
    return `${this.baseUrl}/api/images/${eventId}`;
  }

  async getMetrics() {
    const url = `${this.baseUrl}/api/metrics`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[API] Metrics request failed:', error);
      throw error;
    }
  }

  async getHealth() {
    const url = `${this.baseUrl}/api/health`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[API] Health check failed:', error);
      throw error;
    }
  }
}

export default ApiClient;