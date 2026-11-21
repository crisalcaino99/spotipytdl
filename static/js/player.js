import { fmtTime } from './ui.js';

/**
 * Owns the <audio> element and the play queue.
 *
 * It renders its own bar and repaints only itself on high-frequency events
 * (`timeupdate` fires about four times a second). The shared store is notified
 * only when the *current track* changes, so the track table is not rebuilt on
 * every progress tick.
 */
export function createPlayer(root, store) {
  const audio = new Audio();
  audio.preload = 'metadata';
  audio.volume = Number(localStorage.getItem('spotipyt.volume') ?? 0.8);

  let queue = [];
  let index = -1;

  const current = () => (index >= 0 && index < queue.length ? queue[index] : null);

  root.innerHTML = `
    <div class="player-inner">
      <div class="player-track">
        <span class="p-title" id="p-title">Nothing playing</span>
        <span class="p-artist" id="p-artist"></span>
      </div>
      <div class="player-controls">
        <button id="p-prev" class="icon" title="Previous">⏮</button>
        <button id="p-toggle" class="icon primary" title="Play / pause">▶</button>
        <button id="p-next" class="icon" title="Next">⏭</button>
      </div>
      <div class="player-seek">
        <span id="p-time">0:00</span>
        <input id="p-seek" type="range" min="0" max="1000" value="0" step="1" aria-label="Seek">
        <span id="p-duration">0:00</span>
      </div>
      <div class="player-volume">
        <input id="p-volume" type="range" min="0" max="1" step="0.01" aria-label="Volume">
      </div>
    </div>`;

  const $ = (id) => root.querySelector(id);
  const titleEl = $('#p-title');
  const artistEl = $('#p-artist');
  const toggleEl = $('#p-toggle');
  const seekEl = $('#p-seek');
  const timeEl = $('#p-time');
  const durationEl = $('#p-duration');
  const volumeEl = $('#p-volume');

  volumeEl.value = String(audio.volume);

  function paint() {
    const track = current();
    titleEl.textContent = track ? track.name : 'Nothing playing';
    artistEl.textContent = track ? (track.artists || []).join(', ') : '';
    toggleEl.textContent = audio.paused ? '▶' : '⏸';
    timeEl.textContent = fmtTime(audio.currentTime);
    durationEl.textContent = fmtTime(audio.duration || 0);

    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      seekEl.value = String(Math.round((audio.currentTime / audio.duration) * 1000));
    }
  }

  function load(startIndex, autoplay) {
    index = startIndex;
    const track = current();

    if (!track) {
      audio.removeAttribute('src');
      paint();
      store.set({ playerTrackId: null });
      return;
    }

    audio.src = `/api/tracks/${encodeURIComponent(track.id)}/audio`;
    store.set({ playerTrackId: track.id });
    paint();

    if (autoplay) audio.play().catch(() => paint());
  }

  audio.addEventListener('timeupdate', paint);
  audio.addEventListener('loadedmetadata', paint);
  audio.addEventListener('play', paint);
  audio.addEventListener('pause', paint);
  audio.addEventListener('ended', () => player.next());
  audio.addEventListener('error', () => {
    const track = current();
    if (track) store.set({ notice: `Cannot play "${track.name}" — no local file.` });
  });

  seekEl.addEventListener('input', () => {
    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      audio.currentTime = (Number(seekEl.value) / 1000) * audio.duration;
    }
  });

  volumeEl.addEventListener('input', () => {
    audio.volume = Number(volumeEl.value);
    localStorage.setItem('spotipyt.volume', String(audio.volume));
  });

  const player = {
    /** Play `track`, using `context` as the queue when provided. */
    playTrack(track, context) {
      const list = context && context.length ? context : [track];
      const at = list.findIndex((item) => item.id === track.id);
      queue = list;
      load(at >= 0 ? at : 0, true);
    },

    toggle() {
      if (!current()) return;
      if (audio.paused) audio.play().catch(() => paint());
      else audio.pause();
    },

    next() {
      if (index + 1 < queue.length) load(index + 1, true);
      else {
        audio.pause();
        paint();
      }
    },

    prev() {
      if (index - 1 >= 0) load(index - 1, true);
    },
  };

  toggleEl.addEventListener('click', () => player.toggle());
  $('#p-next').addEventListener('click', () => player.next());
  $('#p-prev').addEventListener('click', () => player.prev());

  paint();
  return player;
}
