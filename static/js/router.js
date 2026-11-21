/**
 * Hash-based routing. No dependency, no history API edge cases.
 *
 *   #/all                     every track in the library
 *   #/playlist/<id>           one playlist
 *   #/search/<query>          filtered track list
 */
export function createRouter(onChange) {
  function parse() {
    const raw = window.location.hash.replace(/^#\/?/, '');
    const [head, ...rest] = raw.split('/');
    const tail = rest.join('/');

    if (head === 'playlist' && tail) {
      return { name: 'playlist', id: decodeURIComponent(tail) };
    }
    if (head === 'search' && tail) {
      return { name: 'search', query: decodeURIComponent(tail) };
    }
    return { name: 'all' };
  }

  window.addEventListener('hashchange', () => onChange(parse()));

  return {
    start() {
      onChange(parse());
    },
    go(hash) {
      window.location.hash = hash;
    },
  };
}
