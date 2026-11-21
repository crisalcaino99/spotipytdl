/**
 * Dead-simple observable state container.
 *
 * One object, a `set()` that shallow-merges, and subscribers. That is the whole
 * "framework". Views read `state` and never mutate it.
 */
export function createStore(initial) {
  let state = { ...initial };
  const listeners = new Set();

  return {
    get state() {
      return state;
    },

    set(patch) {
      state = { ...state, ...patch };
      for (const listener of listeners) listener(state);
    },

    /** Subscribe and immediately receive the current state. */
    subscribe(listener) {
      listeners.add(listener);
      listener(state);
      return () => listeners.delete(listener);
    },
  };
}
