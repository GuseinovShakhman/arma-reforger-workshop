/**
 * utils.js — Shared utility functions.
 */

/**
 * Format bytes as human-readable string (e.g. 24660992 → "23.5 MB").
 */
export function formatBytes(bytes) {
  if (!bytes) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let v = bytes, i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Format a date as relative time ("3 days ago", "just now", etc.).
 */
export function timeAgo(dateStr) {
  if (!dateStr) return "—";
  const diff = Date.now() - new Date(dateStr).getTime();
  const sec  = Math.floor(diff / 1000);
  if (sec < 60)   return "just now";
  const min = Math.floor(sec / 60);
  if (min < 60)   return `${min}m ago`;
  const hr  = Math.floor(min / 60);
  if (hr < 24)    return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 30)   return `${day}d ago`;
  const mo  = Math.floor(day / 30);
  if (mo < 12)    return `${mo}mo ago`;
  return `${Math.floor(mo / 12)}y ago`;
}

/**
 * Copy text to clipboard and show brief confirmation.
 */
export async function copyToClipboard(text, btn) {
  await navigator.clipboard.writeText(text);
  const original = btn.textContent;
  btn.textContent = "Copied!";
  setTimeout(() => { btn.textContent = original; }, 1500);
}

/**
 * Debounce a function call.
 */
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Determine rating CSS class.
 */
export function ratingClass(rating) {
  if (rating == null) return "";
  return rating >= 70 ? "good" : "bad";
}
