// EventFeed component - manages the event feed display
// Handles loading, infinite scroll, and state updates

import eventStore from '../state/EventStore.js';
import { createEventCard } from './EventCard.js';
import ApiClient from '../services/ApiClient.js';
import EventModal from './EventModal.js';

class EventFeed {
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    if (!this.container) {
      console.error('[EventFeed] Container not found:', containerSelector);
      return;
    }

    this.apiClient = new ApiClient();
    this.isLoading = false;
    this.hasMore = true;
    this.offset = 0;
    this.scrollHandler = null;

    // Initialize event modal
    this.eventModal = new EventModal();

    // Expose globally for error retry functionality
    window.eventModal = this.eventModal;

    // Subscribe to state changes
    this.unsubscribe = eventStore.subscribe((state) => {
      this.render(state.events);
    });

    // Setup infinite scroll
    this.setupInfiniteScroll();
  }

  async loadInitialEvents() {
    this.showLoading();

    try {
      const response = await this.apiClient.getEvents({ limit: 100 });
      eventStore.addEvents(response.events || []);
      this.offset = (response.events || []).length;
      this.hasMore = response.total > this.offset;

      console.log(`[EventFeed] Loaded ${this.offset} events, hasMore: ${this.hasMore}`);
    } catch (error) {
      this.showError('Failed to load events. Please refresh the page.');
      console.error('[EventFeed] Load failed:', error);
    } finally {
      this.hideLoading();
    }
  }

  async loadMoreEvents() {
    if (this.isLoading || !this.hasMore) return;

    this.isLoading = true;
    this.showLoadingMore();

    try {
      const response = await this.apiClient.getEvents({
        limit: 50,
        offset: this.offset
      });

      const newEvents = response.events || [];
      eventStore.addEvents(newEvents);
      this.offset += newEvents.length;
      this.hasMore = this.offset < (response.total || 0);

      console.log(`[EventFeed] Loaded ${newEvents.length} more events, total: ${this.offset}, hasMore: ${this.hasMore}`);
    } catch (error) {
      console.error('[EventFeed] Load more failed:', error);
      // Don't show error for infinite scroll failures, just stop loading
    } finally {
      this.isLoading = false;
      this.hideLoadingMore();
    }
  }

  setupInfiniteScroll() {
    this.scrollHandler = () => {
      const scrollTop = this.container.scrollTop;
      const scrollHeight = this.container.scrollHeight;
      const clientHeight = this.container.clientHeight;

      // Trigger when within 200px of bottom
      if (scrollHeight - scrollTop - clientHeight < 200) {
        this.loadMoreEvents();
      }
    };

    this.container.addEventListener('scroll', this.scrollHandler);
  }

  render(events) {
    if (!this.container) return;

    // Clear existing content except loading states
    const loadingState = this.container.querySelector('.loading-state');
    const errorState = this.container.querySelector('.error-state');
    const loadingMore = this.container.querySelector('.loading-more');

    // Preserve loading/error states
    const preservedElements = [];
    if (loadingState) preservedElements.push(loadingState);
    if (errorState) preservedElements.push(errorState);
    if (loadingMore) preservedElements.push(loadingMore);

    // Clear container
    this.container.innerHTML = '';

    // Restore preserved elements
    preservedElements.forEach(el => this.container.appendChild(el));

    if (events.length === 0 && !loadingState && !errorState) {
      this.showEmptyState();
      return;
    }

    // Render event cards
    events.forEach(event => {
      const card = createEventCard(event);

      // Add click handler to open modal
      card.addEventListener('click', () => {
        this.eventModal.open(event.event_id);
      });

      // Make card focusable and indicate it's clickable
      card.setAttribute('tabindex', '0');
      card.setAttribute('role', 'button');
      card.setAttribute('aria-label', `View details for event ${event.event_id}`);

      this.container.appendChild(card);
    });
  }

  showLoading() {
    if (!this.container) return;

    const loadingState = document.createElement('div');
    loadingState.className = 'loading-state';

    loadingState.innerHTML = `
      <div class="spinner" role="status" aria-label="Loading events"></div>
      <p>Loading events...</p>
    `;

    this.container.innerHTML = '';
    this.container.appendChild(loadingState);
  }

  hideLoading() {
    if (!this.container) return;

    const loadingState = this.container.querySelector('.loading-state');
    if (loadingState) {
      loadingState.remove();
    }
  }

  showLoadingMore() {
    if (!this.container) return;

    // Remove existing loading more
    this.hideLoadingMore();

    const loadingMore = document.createElement('div');
    loadingMore.className = 'loading-more';

    loadingMore.innerHTML = `
      <div class="spinner" role="status" aria-label="Loading more events"></div>
      <p>Loading more events...</p>
    `;

    this.container.appendChild(loadingMore);
  }

  hideLoadingMore() {
    if (!this.container) return;

    const loadingMore = this.container.querySelector('.loading-more');
    if (loadingMore) {
      loadingMore.remove();
    }
  }

  showEmptyState() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📹</div>
        <h3>No events yet</h3>
        <p>Waiting for motion detection...</p>
      </div>
    `;
  }

  showError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <h3>Error</h3>
        <p>${message}</p>
        <button class="btn-retry" onclick="location.reload()">Retry</button>
      </div>
    `;
  }

  destroy() {
    // Unsubscribe from state changes
    if (this.unsubscribe) {
      this.unsubscribe();
    }

    // Remove scroll handler
    if (this.scrollHandler && this.container) {
      this.container.removeEventListener('scroll', this.scrollHandler);
    }

    // Destroy event modal
    if (this.eventModal) {
      this.eventModal.destroy();
    }
  }
}

export default EventFeed;