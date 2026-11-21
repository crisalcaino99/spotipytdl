import { api } from '../api.js';
import { artFor, downloadedParam, esc, memo, plural } from '../ui.js';

/**
 * Main panel: playlist hero (when applicable) plus the track table.
 *
 * Playlist tracks arrive unpaginated, so the download filter is applied here.
 * Paginated routes (all tracks, search) filter server-side in main.js.
 */
export function tracksView(root, { store, player, loadMore }) {
  const render = memo(
    (state) => {
      if (state.loadingTracks && state.tracks.length === 0) {
        root.innerHTML = '<p class="muted">Loading…</p>';
        return;
      }

      const isPlaylist = state.route.name === 'playlist';
      const wanted = isPlaylist ? downloadedParam(state.filter) : undefined;

      const all = state.tracks;
      const tracks =
        wanted === undefined
          ? all
          : all.filter((track) => Boolean(track.downloaded) === wanted);

      const downloadedCount = all.filter((track) => track.downloaded).length;

      let header;
      if (isPlaylist) {
        const art = artFor(state.playlistName || state.route.id);
        header = `
          <div class="hero">
            <div class="hero-art" style="${art.style}">${esc(art.initial)}</div>
            <div>
              <span class="hero-kind">Playlist</span>
              <h1>${esc(state.playlistName || 'Playlist')}</h1>
              <div class="hero-meta">
                ${downloadedCount}/${all.length} downloaded ·
                ${plural(all.length, 'track')}
              </div>
            </div>
          </div>`;
      } else {
        const title =
          state.route.name === 'search'
            ? `Results for “${state.route.query}”`
            : 'All tracks';
        header = `
          <div class="content-head">
            <h2>${esc(title)}</h2>
            <span class="muted small">
              ${plural(state.tracksTotal, 'track')} · ${downloadedCount} downloaded
            </span>
          </div>`;
      }

      const remaining = state.tracksTotal - all.length;

      root.innerHTML = `
        ${header}
        <div class="table-wrap">
          <table class="tracks">
            <thead>
              <tr>
                <th class="num">#</th><th>Title</th><th>Artist</th><th>Album</th><th></th>
              </tr>
            </thead>
            <tbody>
              ${
                tracks
                  .map((track, i) => {
                    const playable = Boolean(track.downloaded);
                    const ordinal = track.position != null ? track.position + 1 : i + 1;
                    const action = playable
                      ? `<button class="icon play" data-play="${esc(track.id)}" title="Play">▶</button>`
                      : `<button class="icon" data-download="${esc(track.id)}" title="Download">↓</button>`;
                    const classes = [
                      playable ? 'playable' : '',
                      track.id === state.playerTrackId ? 'playing' : '',
                    ]
                      .filter(Boolean)
                      .join(' ');

                    return `
                      <tr data-id="${esc(track.id)}" class="${classes}">
                        <td class="num">
                          <span class="idx">${ordinal}</span><span class="glyph">▶</span>
                        </td>
                        <td>
                          <span class="title">${esc(track.name)}</span>
                          ${playable ? '' : '<span class="tag">missing</span>'}
                        </td>
                        <td class="muted">${esc((track.artists || []).join(', '))}</td>
                        <td class="muted">${esc(track.album || '')}</td>
                        <td class="actions">${action}</td>
                      </tr>`;
                  })
                  .join('') ||
                '<tr><td colspan="5" class="muted">Nothing matches this filter.</td></tr>'
              }
            </tbody>
          </table>
        </div>
        ${
          state.route.name === 'all' && remaining > 0
            ? `<button class="more" id="more">Load more (${remaining})</button>`
            : ''
        }`;

      const moreButton = root.querySelector('#more');
      if (moreButton) moreButton.addEventListener('click', () => loadMore());
    },
    (state) =>
      [
        state.route.name,
        state.route.id,
        state.route.query,
        state.filter,
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
    if (row && row.classList.contains('playable')) {
      const track = store.state.tracks.find((item) => item.id === row.dataset.id);
      if (track) player.playTrack(track, store.state.tracks);
    }
  });

  return { render };
}
