# Frontend Error Handling

## API Client Error Handler

```javascript
// services/apiClient.js
/**
 * Centralized API client with error handling
 */

const BASE_URL = 'http://localhost:8000/api/v1'

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(message, status, code, details, requestId) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.code = code
    this.details = details
    this.requestId = requestId
  }

  /**
   * Check if error is retryable
   */
  isRetryable() {
    return this.status >= 500 || this.status === 0
  }

  /**
   * Check if error is client-side
   */
  isClientError() {
    return this.status >= 400 && this.status < 500
  }
}

/**
 * Generic API request wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const requestId = generateRequestId()

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId
    }
  }

  try {
    const response = await fetch(url, { ...defaultOptions, ...options })

    // Success response
    if (response.ok) {
      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return await response.json()
      } else if (contentType?.includes('image/')) {
        return await response.blob()
      } else {
        return await response.text()
      }
    }

    // Error response - parse error JSON
    let errorData
    try {
      errorData = await response.json()
    } catch {
      // Response body is not JSON
      errorData = {
        error: {
          code: 'UNKNOWN_ERROR',
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date().toISOString(),
          requestId
        }
      }
    }

    throw new APIError(
      errorData.error.message,
      response.status,
      errorData.error.code,
      errorData.error.details,
      errorData.error.requestId
    )

  } catch (error) {
    // Network error or fetch failure
    if (error instanceof APIError) {
      throw error
    }

    // Network timeout, offline, or CORS error
    throw new APIError(
      'Network request failed. Please check your connection.',
      0,  // Status 0 indicates network error
      'NETWORK_ERROR',
      { originalError: error.message },
      requestId
    )
  }
}

/**
 * Generate unique request ID
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Exported API methods with retry logic
 */
export const api = {
  async events(filters = {}, retries = 2) {
    let lastError
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const params = new URLSearchParams(filters)
        return await apiRequest(`/events?${params}`)
      } catch (error) {
        lastError = error

        // Don't retry client errors (4xx)
        if (error.isClientError && error.isClientError()) {
          throw error
        }

        // Retry server errors with exponential backoff
        if (attempt < retries && error.isRetryable && error.isRetryable()) {
          const delay = Math.pow(2, attempt) * 1000
          console.log(`Request failed, retrying in ${delay}ms...`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
      }
    }
    throw lastError
  },

  async getEvent(eventId) {
    return await apiRequest(`/events/${eventId}`)
  },

  async getEventImage(eventId) {
    return await apiRequest(`/events/${eventId}/image`)
  },

  async health() {
    return await apiRequest('/health')
  },

  async metrics() {
    return await apiRequest('/metrics')
  }
}
```

## UI Error Display Component

```javascript
// components/ErrorBanner.js
/**
 * Error banner component for displaying API errors to users
 */
export function ErrorBanner(error, onRetry, onDismiss) {
  const banner = document.createElement('div')
  banner.className = 'error-banner'

  // Determine error severity and styling
  const severity = error.isClientError ? error.isClientError() ? 'warning' : 'error' : 'error'
  banner.classList.add(`error-banner--${severity}`)

  // User-friendly error message
  const userMessage = getUserFriendlyMessage(error)

  banner.innerHTML = `
    <div class="error-banner__content">
      <span class="error-banner__icon">${getErrorIcon(severity)}</span>
      <div class="error-banner__message">
        <strong>${userMessage}</strong>
        ${error.details ? `<p class="error-banner__details">${formatDetails(error.details)}</p>` : ''}
      </div>
      <div class="error-banner__actions">
        ${error.isRetryable && error.isRetryable() ?
          '<button class="btn btn--retry">Retry</button>' : ''}
        <button class="btn btn--dismiss">Dismiss</button>
      </div>
    </div>
  `

  // Attach event listeners
  if (error.isRetryable && error.isRetryable()) {
    banner.querySelector('.btn--retry').addEventListener('click', onRetry)
  }
  banner.querySelector('.btn--dismiss').addEventListener('click', () => {
    banner.remove()
    if (onDismiss) onDismiss()
  })

  return banner
}

/**
 * Convert technical error to user-friendly message
 */
function getUserFriendlyMessage(error) {
  const messages = {
    'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection.',
    'DATABASE_ERROR': 'Database is temporarily unavailable. Please try again in a moment.',
    'RESOURCE_NOT_FOUND': 'The requested item could not be found.',
    'INVALID_PARAMETERS': 'Invalid request. Please check your input.',
    'SERVICE_UNAVAILABLE': 'Service is temporarily unavailable. Please try again later.',
    'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.'
  }

  return messages[error.code] || error.message || messages['UNKNOWN_ERROR']
}

/**
 * Get icon for error severity
 */
function getErrorIcon(severity) {
  const icons = {
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️'
  }
  return icons[severity] || icons['error']
}

/**
 * Format error details for display
 */
function formatDetails(details) {
  if (typeof details === 'string') return details
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ')
}
```

## Usage Example in Component

```javascript
// components/EventTimeline.js
import { api, APIError } from '../services/apiClient.js'
import { ErrorBanner } from './ErrorBanner.js'
import { appState } from '../services/stateManager.js'

export function EventTimeline() {
  const container = document.createElement('div')
  container.className = 'event-timeline'

  // Load events
  loadEvents(container)

  return container
}

async function loadEvents(container) {
  // Show loading state
  container.innerHTML = '<div class="loading">Loading events...</div>'

  try {
    const data = await api.events({ limit: 100 })
    appState.setState('events', data.events)
    renderEvents(container, data.events)

  } catch (error) {
    if (error instanceof APIError) {
      // Display error banner with retry
      const errorBanner = ErrorBanner(
        error,
        () => loadEvents(container),  // Retry callback
        () => container.innerHTML = '<p>Unable to load events</p>'
      )
      container.innerHTML = ''
      container.appendChild(errorBanner)

      // Log error for debugging
      console.error('Failed to load events:', {
        code: error.code,
        message: error.message,
        requestId: error.requestId,
        details: error.details
      })
    } else {
      // Unexpected error
      console.error('Unexpected error loading events:', error)
      container.innerHTML = '<div class="error">An unexpected error occurred</div>'
    }
  }
}

function renderEvents(container, events) {
  // Render event list
  container.innerHTML = ''
  events.forEach(event => {
    const card = EventCard(event, handleEventClick)
    container.appendChild(card)
  })
}
```

---
