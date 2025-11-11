// EventCard component - renders individual event cards
// Handles event card creation and image loading with fallbacks

import ApiClient from '../services/ApiClient.js';
import { formatTimestamp, formatConfidence } from '../utils/formatters.js';

const apiClient = new ApiClient();

export function createEventCard(event) {
  const card = document.createElement('article');
  card.className = 'event-card';
  card.setAttribute('data-event-id', event.event_id);
  card.setAttribute('role', 'article');
  card.setAttribute('aria-label', `Event from ${event.camera_id} at ${formatTimestamp(event.timestamp)}`);

  // Image container
  const imageContainer = document.createElement('div');
  imageContainer.className = 'event-card-image';

  const img = document.createElement('img');
  img.src = apiClient.getImageUrl(event.event_id);
  img.alt = `Event from ${event.camera_id}`;
  img.loading = 'lazy';
  img.onerror = () => {
    // Fallback to placeholder on error
    img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjM2EzYTNhIi8+Cjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM4MDgwODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7ilrDwn5iA8L3RGV4dD4KPC9zdmc+';
    img.alt = 'Image not available';
  };

  imageContainer.appendChild(img);

  // Card content
  const content = document.createElement('div');
  content.className = 'event-card-content';

  // Header
  const header = document.createElement('div');
  header.className = 'event-card-header';

  const cameraId = document.createElement('span');
  cameraId.className = 'camera-id';
  cameraId.textContent = event.camera_id;

  const timestamp = document.createElement('time');
  timestamp.className = 'timestamp';
  timestamp.setAttribute('datetime', event.timestamp);
  timestamp.textContent = formatTimestamp(event.timestamp);

  header.appendChild(cameraId);
  header.appendChild(timestamp);

  // Detected objects section
  const objectsSection = document.createElement('div');
  objectsSection.className = 'detected-objects';

  const objects = parseDetectedObjects(event.detected_objects);

  if (objects.length > 0) {
    const countText = document.createElement('p');
    countText.className = 'objects-count';
    countText.textContent = `${objects.length} object${objects.length > 1 ? 's' : ''} detected:`;
    objectsSection.appendChild(countText);

    const objectsList = document.createElement('ul');
    objectsList.className = 'objects-list';

    objects.forEach(obj => {
      const li = document.createElement('li');

      const nameSpan = document.createElement('span');
      nameSpan.className = 'object-name';
      nameSpan.textContent = obj.name;

      const confidenceSpan = document.createElement('span');
      confidenceSpan.className = 'object-confidence';
      confidenceSpan.textContent = formatConfidence(obj.confidence);

      li.appendChild(nameSpan);
      li.appendChild(confidenceSpan);
      objectsList.appendChild(li);
    });

    objectsSection.appendChild(objectsList);
  } else {
    const noObjects = document.createElement('p');
    noObjects.className = 'objects-count';
    noObjects.textContent = 'No objects detected';
    objectsSection.appendChild(noObjects);
  }

  // Assemble card
  content.appendChild(header);
  content.appendChild(objectsSection);
  card.appendChild(imageContainer);
  card.appendChild(content);

  // Add click handler for future modal (Story 5.7)
  card.addEventListener('click', () => {
    console.log('[EventCard] Event clicked:', event.event_id);
    // TODO: Open event detail modal (Story 5.7)
  });

  // Add keyboard support
  card.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      card.click();
    }
  });

  card.setAttribute('tabindex', '0');

  // Fade-in animation for new events
  card.style.animation = 'fadeIn 0.3s ease-in';

  return card;
}

function parseDetectedObjects(jsonString) {
  if (!jsonString) return [];

  try {
    const objects = JSON.parse(jsonString);

    // Ensure it's an array and has the expected structure
    if (!Array.isArray(objects)) return [];

    // Sort by confidence (highest first)
    return objects
      .filter(obj => obj && typeof obj.name === 'string' && typeof obj.confidence === 'number')
      .sort((a, b) => b.confidence - a.confidence);
  } catch (error) {
    console.error('[EventCard] Failed to parse detected_objects:', error);
    return [];
  }
}