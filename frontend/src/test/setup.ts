import '@testing-library/jest-dom';

// Polyfill window.HTMLElement.prototype.scrollIntoView if not present in jsdom
if (typeof window !== 'undefined' && !window.HTMLElement.prototype.scrollIntoView) {
  window.HTMLElement.prototype.scrollIntoView = () => {};
}
