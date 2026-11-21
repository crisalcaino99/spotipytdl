import { api } from './api.js';
import { createPlayer } from './player.js';
import { createRouter } from './router.js';
import { createStore } from './store.js';
import { downloadsView } from './views/downloads.js';
import { playlistsView } from './views/playlists.js';
import { tracksView } from './views/tracks.js';

/**
 * Wiring. Everything interesting happens in the modules this file imports.
 *
 * Adding a view:
 *   1. create static/js/views/thing.js exporting `(root, ctx) => ({ render })`
 *   2. add a container element in index.html
 *   3. import it here, push it into `views`, done
 */

const PAGE_SIZE = 200;

const store = createStore({
  route: { name: 'all' },
  stats: null,
  playlists: [],
  tracks: [],
  tracksTotal: 0,
  playlistName: null,
  loadingTracks: false,
  jobs: [],
  playerTrackId: null,
  notice: null,
});

const player = createPlayer(document.getElementById('player'), store);

let loaded = 0;

async function loadMore() {
  const route = store.state.route;

  try {
    const data = await api.tracks({
      q: route.name === 'search' ? route.query : '',
      limit: PAGE_SIZE,
      offset: loaded,
    });

    const tracks = loaded === 0 ? data.items : [...store.state.tracks, ...data.items];
    loaded = tracks.length;

    store.set({ tracks, tracksTotal: data.total, loadingTracks: false });
  } catch (error) {
    fail(error);
  }
}

async function loadRoute(route) {
  store.set({ loadingTracks: true, tracks: [], tracksTotal: 0, playlistName: null });
  loaded = 0;

  if (route.name !== 'playlist') {
    await loadMore();
    return;
  }

  try {
    const data = await api.playlist(route.id);
    const name =
      String(data.playlist?.name || '').trim() ||
      `Untitled (${String(route.id).slice(0, 6)}…)`;

    store.set({
      tracks: data.tracks,
      tracksTotal: data.tracks.length,
      playlistName: name,
      loadingTracks: false,
    });
  } catch (error) {
    fail(error);
  }
}

function fail(error) {
  console.error(error);
  store.set({ loadingTracks: false, notice: error.message });
}

const router = createRouter((route) => {
  store.set({ route });
  loadRoute(route);
});

const ctx = { api, store, player, loadMore };

const views = [
  playlistsView(document.getElementById('playlists'), ctx),
  tracksView(document.getElementById('content'), ctx),
  downloadsView(document.getElementById('downloads'), ctx),
];

store.subscribe((state) => {
  for (const view of views) view.render(state);

  const notice = document.getElementById('notice');
  if (notice) {
    notice.textContent = state.notice || '';
    notice.classList.toggle('visible', Boolean(state.notice));
  }
});

document.getElementById('search-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const query = document.getElementById('q').value.trim();
  window.location.hash = query ? `#/search/${encodeURIComponent(query)}` : '#/all';
});

async function refreshSidebar() {
  try {
    const [stats, playlists] = await Promise.all([api.stats(), api.playlists()]);
    store.set({ stats, playlists });
    document.getElementById('stats').textContent =
      `${stats.downloaded_tracks}/${stats.total_tracks} downloaded · ` +
      `${stats.total_playlists} playlists · ${stats.total_albums} albums`;
  } catch (error) {
    fail(error);
  }
}

async function refreshJobs() {
  try {
    const data = await api.downloads();
    store.set({ jobs: data.items });
  } catch {
    /* keep polling: the server may just be restarting */
  }
}

router.start();
refreshSidebar();
refreshJobs();
setInterval(refreshJobs, 2000);
setInterval(refreshSidebar, 15000);
