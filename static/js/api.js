/**
 * Every HTTP call the UI makes lives here.
 *
 * If you change a backend route, this is the only file that needs to know.
 */

async function request(path, init) {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = body.detail;
    } catch {
      /* response had no JSON body; the status line is enough */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  stats: () => request('/api/stats'),

  playlists: () => request('/api/playlists').then((data) => data.items),

  playlist: (id) => request(`/api/playlists/${encodeURIComponent(id)}`),

  tracks({ q = '', limit = 200, offset = 0, downloaded } = {}) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (q) params.set('q', q);
    if (downloaded != null) params.set('downloaded', String(downloaded));
    return request(`/api/tracks?${params}`);
  },

  enqueue: (payload) =>
    request('/api/downloads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  downloads: () => request('/api/downloads'),

  cancel: (id) => request(`/api/downloads/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  audioUrl: (trackId) => `/api/tracks/${encodeURIComponent(trackId)}/audio`,
};
