import { api } from '../api.js';
import { esc, memo, plural } from '../ui.js';

/**
 * Main panel: the track table.
 *
 * Downloaded tracks get a play button; everything else gets a download button.
 * Click handlers are delegated from the container, so the table can be
 * re-rendered freely without re-binding listeners.
 */
export function tracksView(root, { store, player, loadMore }) {
  const render = memo(
    (state) => {
      const tracks = state.tracks;

      if (state.loadingTracks && tracks.length === 0) {
        root.innerHTML = '<p class="muted">Loading…</p>';
        return;
      }

      let title = 'All tracks';
      if (state.route.name === 'playlist') title = state.playlistName || 'Playlist';
      if (state.route.name === 'search') title = `Search: ${state.route.query}`;

      const remaining = state.tracksTotal - tracks.length;

      root.innerHTML = `
        <div class="content-head">
          <h2>${esc(title)}</h2>
          <span class="muted small">${plural(state.tracksTotal, 'track')}</span>
        </div>
        <div class="table-wrap">
          <table class="tracks">
            <thead>
              <tr><th class="num">#</th><th>Title</th><th>Artist</th><th>Album</th><th></th></tr>
            </thead>
            <tbody>
              ${tracks
                .map((track, i) => {
                  const isPlaying = track.id === state.playerTrackId;
                  const ordinal = track.position != null ? track.position + 1 : i + 1;
                  const action = track.downloaded
                    ? `<button class="icon play" data-play="${esc(track.id)}" title="Play">▶</button>`
                    : `<button class="icon" data-download="${esc(track.id)}" title="Download">↓</button>`;

                  return `
                    <tr data-id="${esc(track.id)}" class="${isPlaying ? 'playing' : ''}">
                      <td class="muted num">${ordinal}</td>
                      <td>
                        <span class="title">${esc(track.name)}</span>
                        ${track.downloaded ? '' : '<span class="tag">not downloaded</span>'}
                      </td>
                      <td class="muted">${esc((track.artists || []).join(', '))}</td>
                      <td class="muted">${esc(track.album || '')}</td>
                      <td class="actions">${action}</td>
                    </tr>`;
                })
                .join('')}
            </tbody>
          </table>
        </div>
        ${
          state.route.name === 'all' && remaining > 0
            ? `<button class="more" id="more">Load more (${remaining} left)</button>`
            : ''
        }`;

      const moreButton = root.querySelector('#more');
      if (moreButton) moreButton.addEventListener('click', () => loadMore());
    },
    (state) => [
      state.route.name,
      state.route.id,
      state.route.query,
      state.tracks.length,
      state.tracksTotal,
      state.playlistName,
      state.playerTrackId,
      state.loadingTracks,
      state.tracks.map((track) => (track.downloaded ? 1 : 0)).join(''),
    ].join('|'),
  );

  root.addEventListener('click', async (event) => {
    const playButton = event.target.closest('[data-play]');
    if (playButton) {
      const track = store.state.tracks.find((item) => item.id === playButton.dataset.play);
      if (track) player.playTrack(track, store.state.tracks);
      return;
    }

    const downloadButton = event.target.closest('[data-download]');
    if (downloadButton) {
      downloadButton.disabled = true;
      try {
        await api.enqueue({ track_ids: [downloadButton.dataset.download] });
      } catch (error) {
        store.set({ notice: error.message });
      }
      return;
    }

    const row = event.target.closest('tr[data-id]');
    if (row) {
      const track = store.state.tracks.find((item) => item.id === row.dataset.id);
      if (track && track.downloaded) player.playTrack(track, store.state.tracks);
    }
  });

  return { render };
}
