import { artFor, esc, memo, playlistLabel } from '../ui.js';

/**
 * Sidebar library list.
 *
 * Respects the global download filter: "downloaded" hides playlists with
 * nothing downloaded, "missing" hides fully-downloaded ones.
 */
export function playlistsView(root, { store }) {
  const filterInput = document.getElementById('filter');

  const render = memo(
    (state) => {
      const needle = filterInput.value.trim().toLowerCase();
      let items = state.playlists;

      if (state.filter === 'downloaded') {
        items = items.filter((playlist) => (playlist.downloaded || 0) > 0);
      } else if (state.filter === 'missing') {
        items = items.filter(
          (playlist) => (playlist.tracks || 0) > (playlist.downloaded || 0),
        );
      }

      if (needle) {
        items = items.filter((playlist) => {
          const label = playlistLabel(playlist).toLowerCase();
          const owner = String(playlist.owner || '').toLowerCase();
          return label.includes(needle) || owner.includes(needle);
        });
      }

      root.innerHTML =
        items
          .map((playlist) => {
            const art = artFor(playlistLabel(playlist));
            const total = playlist.tracks ?? playlist.total_tracks ?? 0;
            const done = playlist.downloaded ?? 0;
            const complete = total > 0 && done >= total;
            const active =
              state.route.name === 'playlist' && state.route.id === playlist.id
                ? ' active'
                : '';

            return `
              <a class="pl-item${active}" href="#/playlist/${encodeURIComponent(playlist.id)}">
                <span class="pl-art" style="${art.style}">${esc(art.initial)}</span>
                <span class="pl-text">
                  <span class="pl-name">${esc(playlistLabel(playlist))}</span>
                  <span class="pl-meta">
                    <span class="${complete ? 'complete' : ''}">${done}/${total}</span> downloaded
                  </span>
                </span>
              </a>`;
          })
          .join('') || '<p class="muted small" style="padding:0 8px">Nothing here.</p>';
    },
    (state) =>
      [
        state.route.name,
        state.route.id,
        state.filter,
        state.playlists.length,
        state.playlists
          .map((playlist) => `${playlist.id}:${playlist.downloaded || 0}:${playlist.tracks || 0}`)
          .join(','),
        filterInput.value,
      ].join('|'),
  );

  filterInput.addEventListener('input', () => render(store.state));

  return { render };
}
