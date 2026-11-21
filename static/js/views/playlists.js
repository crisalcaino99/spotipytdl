import { esc, memo, playlistLabel } from '../ui.js';

/**
 * Sidebar: "All tracks" plus every playlist, with a client-side filter.
 *
 * View contract: `(root, ctx) => ({ render(state) })`
 */
export function playlistsView(root, { store }) {
  const filterInput = document.getElementById('filter');

  const render = memo(
    (state) => {
      const needle = filterInput.value.trim().toLowerCase();

      const matches = state.playlists.filter((playlist) => {
        const label = playlistLabel(playlist).toLowerCase();
        const owner = String(playlist.owner || '').toLowerCase();
        return !needle || label.includes(needle) || owner.includes(needle);
      });

      const activeAll = state.route.name === 'all' ? ' active' : '';

      root.innerHTML = `
        <a class="nav-item${activeAll}" href="#/all">
          <span>All tracks</span>
          <em>${state.stats ? state.stats.total_tracks : ''}</em>
        </a>
        ${matches
          .map((playlist) => {
            const active =
              state.route.name === 'playlist' && state.route.id === playlist.id
                ? ' active'
                : '';
            return `
              <a class="nav-item${active}"
                 href="#/playlist/${encodeURIComponent(playlist.id)}">
                <span>${esc(playlistLabel(playlist))}</span>
                <em>${playlist.total_tracks ?? ''}</em>
              </a>`;
          })
          .join('')}
        ${matches.length ? '' : '<p class="muted small">No playlists match.</p>'}`;
    },
    (state) => [
      state.route.name,
      state.route.id,
      state.playlists.length,
      state.stats ? state.stats.total_tracks : 0,
      filterInput.value,
    ].join('|'),
  );

  filterInput.addEventListener('input', () => render(store.state));

  return { render };
}
