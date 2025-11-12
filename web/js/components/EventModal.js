/**
 * Event Detail Modal Component
 * Displays full event details in a modal overlay
 */

import ApiClient from '../services/ApiClient.js';
import eventStore from '../state/EventStore.js';
import { formatTimestamp, formatBytes } from '../utils/formatters.js';
import { trapFocus, removeFocusTrap, restoreFocus } from '../utils/focusTrap.js';

class EventModal {
  constructor() {
    this.modal = null;
    this.overlay = null;
    this.currentEventId = null;
    this.currentEventIndex = -1;
    this.apiClient = new ApiClient();
    this.previousFocusedElement = null;

    this.createModal();
    this.attachEventListeners();

    console.log('[EventModal] Initialized');
  }

  /**
   * Creates the modal DOM structure
   */
  createModal() {
    // Modal overlay
    this.overlay = document.createElement('div');
    this.overlay.className = 'modal-overlay';
    this.overlay.style.display = 'none';
    this.overlay.setAttribute('aria-hidden', 'true');

    // Modal dialog
    this.modal = document.createElement('div');
    this.modal.className = 'modal-dialog';
    this.modal.setAttribute('role', 'dialog');
    this.modal.setAttribute('aria-modal', 'true');
    this.modal.setAttribute('aria-label', 'Event Details');

    // Modal content (will be populated dynamically)
    this.modal.innerHTML = `
      <button class="modal-close" aria-label="Close dialog">✕</button>
      <div class="modal-content"></div>
      <div class="modal-navigation">
        <button class="btn-prev" aria-label="Previous event">← Previous</button>
        <button class="btn-next" aria-label="Next event">Next →</button>
      </div>
    `;

    this.overlay.appendChild(this.modal);
    document.body.appendChild(this.overlay);
  }

  /**
   * Attaches event listeners for modal interactions
   */
  attachEventListeners() {
    // Close button
    const closeBtn = this.modal.querySelector('.modal-close');
    closeBtn.addEventListener('click', () => this.close());

    // Click outside to close
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.close();
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (!this.isOpen()) return;

      if (e.key === 'Escape') {
        this.close();
      } else if (e.key === 'ArrowLeft') {
        this.navigateToPrevious();
      } else if (e.key === 'ArrowRight') {
        this.navigateToNext();
      }
    });

    // Prev/Next buttons
    const prevBtn = this.modal.querySelector('.btn-prev');
    const nextBtn = this.modal.querySelector('.btn-next');

    prevBtn.addEventListener('click', () => this.navigateToPrevious());
    nextBtn.addEventListener('click', () => this.navigateToNext());
  }

  /**
   * Opens the modal for a specific event
   * @param {string} eventId - The event ID to display
   */
  async open(eventId) {
    console.log('[EventModal] Opening modal for event:', eventId);

    this.currentEventId = eventId;
    this.currentEventIndex = this.findEventIndex(eventId);

    // Store previous focus
    this.previousFocusedElement = document.activeElement;

    // Show modal
    this.overlay.style.display = 'flex';
    this.overlay.setAttribute('aria-hidden', 'false');

    // Disable body scroll
    document.body.style.overflow = 'hidden';

    // Show loading state
    this.showLoading();

    // Fetch event details
    await this.loadEventDetails(eventId);

    // Focus on close button
    const closeBtn = this.modal.querySelector('.modal-close');
    closeBtn.focus();

    // Trap focus within modal
    trapFocus(this.modal);

    // Update prev/next button states
    this.updateNavigationButtons();
  }

  /**
   * Closes the modal
   */
  close() {
    console.log('[EventModal] Closing modal');

    // Hide modal
    this.overlay.style.display = 'none';
    this.overlay.setAttribute('aria-hidden', 'true');

    // Restore body scroll
    document.body.style.overflow = '';

    // Remove focus trap
    removeFocusTrap(this.modal);

    // Restore focus
    if (this.previousFocusedElement) {
      restoreFocus(this.previousFocusedElement);
    }

    this.currentEventId = null;
    this.currentEventIndex = -1;
  }

  /**
   * Checks if the modal is currently open
   * @returns {boolean} True if modal is open
   */
  isOpen() {
    return this.overlay.style.display !== 'none';
  }

  /**
   * Loads and displays event details
   * @param {string} eventId - The event ID to load
   */
  async loadEventDetails(eventId) {
    const content = this.modal.querySelector('.modal-content');

    try {
      // Fetch from API (or get from event store)
      const event = await this.getEventDetails(eventId);

      // Render event details
      content.innerHTML = this.renderEventDetails(event);

      console.log('[EventModal] Event details loaded');
    } catch (error) {
      console.error('[EventModal] Failed to load event details:', error);
      this.showError();
    }
  }

  /**
   * Gets event details from store or API
   * @param {string} eventId - The event ID to fetch
   * @returns {Object} Event data
   */
  async getEventDetails(eventId) {
    // First, try to get from event store (already loaded)
    const state = eventStore.getState();
    const cachedEvent = state.events.find(e => e.event_id === eventId);

    if (cachedEvent) {
      console.log('[EventModal] Using cached event from store');
      return cachedEvent;
    }

    // If not in store, fetch from API
    console.log('[EventModal] Fetching event from API:', eventId);
    const response = await this.apiClient.getEvent(eventId);
    return response;
  }

  /**
   * Renders the event details HTML
   * @param {Object} event - The event data
   * @returns {string} HTML string
   */
  renderEventDetails(event) {
    // Use the full image path from the event data, prefixed with base URL
    const imageUrl = `${this.apiClient.baseUrl}${event.image_path}`;
    const objects = this.parseDetectedObjects(event.detected_objects);

    return `
      <div class="modal-image-container">
        <img
          src="${imageUrl}"
          alt="Event from ${event.camera_id}"
          class="modal-image"
          onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22800%22 height=%22600%22%3E%3Crect fill=%22%233a3a3a%22 width=%22800%22 height=%22600%22/%3E%3Ctext fill=%22%23808080%22 x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2224%22%3ENo Image Available%3C/text%3E%3C/svg%3E'"
        />
      </div>

      <div class="modal-details">
        <h2 class="modal-title">${event.camera_id}</h2>
        <p class="modal-timestamp">${formatTimestamp(event.timestamp)}</p>

        <div class="detail-section">
          <h3>Event Information</h3>
          <dl class="detail-list">
            <dt>Event ID</dt>
            <dd>${event.event_id}</dd>

            <dt>Camera</dt>
            <dd>${event.camera_id}</dd>

            <dt>Timestamp</dt>
            <dd>${formatTimestamp(event.timestamp)}</dd>

            <dt>Image Path</dt>
            <dd><code>${event.image_path}</code></dd>
          </dl>
        </div>

        <div class="detail-section">
          <h3>Detected Objects</h3>
          ${objects.length > 0 ? `
            <ul class="objects-list-detailed">
              ${objects.map(obj => `
                <li class="object-item">
                  <span class="object-name">${obj.name}</span>
                  <span class="object-confidence">${Math.round(obj.confidence * 100)}%</span>
                  <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${obj.confidence * 100}%"></div>
                  </div>
                </li>
              `).join('')}
            </ul>
          ` : `
            <p class="no-objects">No objects detected</p>
          `}
        </div>
      </div>
    `;
  }

  /**
   * Parses detected objects from JSON string
   * @param {string} jsonString - JSON string of detected objects
   * @returns {Array} Array of parsed objects
   */
  parseDetectedObjects(jsonString) {
    if (!jsonString) return [];

    try {
      const objects = JSON.parse(jsonString);
      return objects.sort((a, b) => b.confidence - a.confidence);
    } catch (error) {
      console.error('[EventModal] Failed to parse detected_objects:', error);
      return [];
    }
  }

  /**
   * Finds the index of an event in the event store
   * @param {string} eventId - The event ID to find
   * @returns {number} The event index, or -1 if not found
   */
  findEventIndex(eventId) {
    const state = eventStore.getState();
    return state.events.findIndex(e => e.event_id === eventId);
  }

  /**
   * Navigates to the previous event
   */
  navigateToPrevious() {
    const state = eventStore.getState();
    const prevIndex = this.currentEventIndex - 1;

    if (prevIndex >= 0) {
      const prevEvent = state.events[prevIndex];
      this.currentEventId = prevEvent.event_id;
      this.currentEventIndex = prevIndex;
      this.loadEventDetails(prevEvent.event_id);
      this.updateNavigationButtons();
    }
  }

  /**
   * Navigates to the next event
   */
  navigateToNext() {
    const state = eventStore.getState();
    const nextIndex = this.currentEventIndex + 1;

    if (nextIndex < state.events.length) {
      const nextEvent = state.events[nextIndex];
      this.currentEventId = nextEvent.event_id;
      this.currentEventIndex = nextIndex;
      this.loadEventDetails(nextEvent.event_id);
      this.updateNavigationButtons();
    }
  }

  /**
   * Updates the state of navigation buttons
   */
  updateNavigationButtons() {
    const state = eventStore.getState();
    const prevBtn = this.modal.querySelector('.btn-prev');
    const nextBtn = this.modal.querySelector('.btn-next');

    // Disable "Previous" if first event
    if (this.currentEventIndex <= 0) {
      prevBtn.disabled = true;
      prevBtn.classList.add('disabled');
    } else {
      prevBtn.disabled = false;
      prevBtn.classList.remove('disabled');
    }

    // Disable "Next" if last event
    if (this.currentEventIndex >= state.events.length - 1) {
      nextBtn.disabled = true;
      nextBtn.classList.add('disabled');
    } else {
      nextBtn.disabled = false;
      nextBtn.classList.remove('disabled');
    }
  }

  /**
   * Shows loading state
   */
  showLoading() {
    const content = this.modal.querySelector('.modal-content');
    content.innerHTML = `
      <div class="modal-loading">
        <div class="spinner"></div>
        <p>Loading event details...</p>
      </div>
    `;
  }

  /**
   * Shows error state
   */
  showError() {
    const content = this.modal.querySelector('.modal-content');
    content.innerHTML = `
      <div class="modal-error">
        <div class="error-icon">⚠️</div>
        <h3>Failed to load event details</h3>
        <p>The event could not be loaded. Please try again.</p>
        <button class="btn-retry" onclick="window.eventModal.loadEventDetails('${this.currentEventId}')">Retry</button>
      </div>
    `;
  }

  /**
   * Destroys the modal and cleans up resources
   */
  destroy() {
    console.log('[EventModal] Destroying modal');

    // Remove from DOM
    if (this.overlay && this.overlay.parentNode) {
      this.overlay.parentNode.removeChild(this.overlay);
    }

    // Clean up references
    this.modal = null;
    this.overlay = null;
    this.currentEventId = null;
    this.currentEventIndex = -1;
    this.previousFocusedElement = null;
  }
}

export default EventModal;