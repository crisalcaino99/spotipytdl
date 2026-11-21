import { api } from './api.js';
import { createPlayer } from './player.js';
import { createRouter } from './router.js';
import { createStore } from './store.js';
import { downloadedParam } from './ui.js';
import { downloadsView } from './views/downloads.js';
import { playlistsView } from './views/playlists.js';
import { tracksView } from './views/tracks.js';

/**
 * Wiring only. Everything interesting lives in the imported modules.
 *
 * To add a view: create static/js/views/thing.js exporting
 * `(root, ctx) => ({ render })`, add a container in index.html, import it
 * here and push it onto `views`.
 */

const PAGE_SIZE = 200;

const store = createStore({
  route: { name: 'all' },
  filter: 'all', // 'all' | 'downloaded' | 'missing'
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
  const { route, filter } = store.state;

  try {
    const data = await api.tracks({
      q: route.name === 'search' ? route.query : '',
      downloaded: downloadedParam(filter),
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

  // Playlist tracks arrive in one response, so the download filter is applied
  // in the view. Paginated routes filter server-side instead.
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
  notice.textContent = state.notice || '';
  notice.classList.toggle('visible', Boolean(state.notice));

  const allCount = document.getElementById('nav-all-count');
  if (allCount && state.stats) allCount.textContent = String(state.stats.total_tracks);

  const navAll = document.getElementById('nav-all');
  if (navAll) navAll.classList.toggle('active', state.route.name === 'all');
});

/* filters -------------------------------------------------------------- */

const segmented = document.getElementById('segmented');

segmented.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-filter]');
  if (!button || button.dataset.filter === store.state.filter) return;

  for (const item of segmented.querySelectorAll('button')) {
    item.classList.toggle('active', item === button);
  }

  store.set({ filter: button.dataset.filter });
  loadRoute(store.state.route);
});

/* search --------------------------------------------------------------- */

document.getElementById('search-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const query = document.getElementById('q').value.trim();
  window.location.hash = query ? `#/search/${encodeURIComponent(query)}` : '#/all';
});

/* polling -------------------------------------------------------------- */

async function refreshSidebar() {
  try {
    const [stats, playlists] = await Promise.all([api.stats(), api.playlists()]);
    store.set({ stats, playlists });
    document.getElementById('stats').textContent =
      `${stats.downloaded_tracks}/${stats.total_tracks} tracks · ` +
      `${stats.total_playlists} playlists`;
  } catch (error) {
    fail(error);
  }
}

async function refreshJobs() {
  try {
    const data = await api.downloads();
    store.set({ jobs: data.items });
  } catch {
    /* the server may be restarting; keep polling */
  }
}

router.start();
refreshSidebar();
refreshJobs();
setInterval(refreshJobs, 2000);
setInterval(refreshSidebar, 15000);
