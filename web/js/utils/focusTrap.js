/**
 * Focus trap utility for modal accessibility
 * Ensures focus stays within a container during keyboard navigation
 */

let focusableElements = [];
let firstFocusableElement = null;
let lastFocusableElement = null;

/**
 * Traps focus within the specified container
 * @param {HTMLElement} container - The container element to trap focus within
 */
export function trapFocus(container) {
  // Get all focusable elements within container
  const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  focusableElements = Array.from(container.querySelectorAll(focusableSelector));

  if (focusableElements.length === 0) {
    console.warn('[FocusTrap] No focusable elements found in container');
    return;
  }

  firstFocusableElement = focusableElements[0];
  lastFocusableElement = focusableElements[focusableElements.length - 1];

  console.log(`[FocusTrap] Trapped focus in container with ${focusableElements.length} focusable elements`);

  // Handle Tab key navigation
  container.addEventListener('keydown', handleFocusTrap);
}

/**
 * Removes focus trap from the container
 * @param {HTMLElement} container - The container element to remove focus trap from
 */
export function removeFocusTrap(container) {
  console.log('[FocusTrap] Removing focus trap');
  container.removeEventListener('keydown', handleFocusTrap);
  focusableElements = [];
  firstFocusableElement = null;
  lastFocusableElement = null;
}

/**
 * Handles focus trap keyboard navigation
 * @param {KeyboardEvent} e - The keyboard event
 */
function handleFocusTrap(e) {
  if (e.key !== 'Tab') return;

  if (e.shiftKey) {
    // Shift + Tab: Move backwards
    if (document.activeElement === firstFocusableElement) {
      e.preventDefault();
      lastFocusableElement.focus();
      console.log('[FocusTrap] Wrapped focus to last element');
    }
  } else {
    // Tab: Move forwards
    if (document.activeElement === lastFocusableElement) {
      e.preventDefault();
      firstFocusableElement.focus();
      console.log('[FocusTrap] Wrapped focus to first element');
    }
  }
}

/**
 * Restores focus to a specific element
 * @param {HTMLElement} element - The element to focus
 */
export function restoreFocus(element) {
  if (element && typeof element.focus === 'function') {
    // Small delay to ensure DOM is ready
    setTimeout(() => {
      element.focus();
      console.log('[FocusTrap] Focus restored to element');
    }, 10);
  }
}

/**
 * Gets all focusable elements in a container (for debugging)
 * @param {HTMLElement} container - The container to check
 * @returns {HTMLElement[]} Array of focusable elements
 */
export function getFocusableElements(container) {
  const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  return Array.from(container.querySelectorAll(focusableSelector));
}