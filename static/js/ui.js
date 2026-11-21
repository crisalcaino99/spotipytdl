/**
 * Small helpers shared by every view. No framework, no dependencies.
 */

/** Escape text before putting it in innerHTML. Always use this on API data. */
export const esc = (value) =>
  String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));

export const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;

export function fmtTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

/** Playlists without a name are real data here; give them a readable label. */
export const playlistLabel = (playlist) =>
  String(playlist.name || '').trim() ||
  `Untitled (${String(playlist.id).slice(0, 6)}…)`;

/**
 * Wrap a render function so it only runs when `keyOf(state)` changes.
 *
 * Without this, the ~4x/second audio progress updates would re-render a
 * 1500-row table. Each view decides what it actually cares about.
 */
export function memo(render, keyOf) {
  let lastKey;
  let started = false;
  return (state) => {
    const key = keyOf(state);
    if (started && key === lastKey) return;
    started = true;
    lastKey = key;
    render(state);
  };
}

export function debounce(fn, ms = 200) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}
