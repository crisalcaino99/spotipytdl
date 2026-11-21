# Frontend

Plain JavaScript ES modules. **No build step, no npm, no framework.** Edit a
file, reload the browser.

## Files

| File | Responsibility |
|---|---|
| `main.js` | wiring: store, router, views, polling |
| `api.js` | every HTTP call — the only file that knows backend routes |
| `store.js` | tiny observable state (`get state`, `set(patch)`, `subscribe`) |
| `router.js` | hash routing: `#/all`, `#/playlist/<id>`, `#/search/<q>` |
| `player.js` | `<audio>`, play queue, the bottom bar |
| `ui.js` | `esc()`, `fmtTime()`, `memo()`, small helpers |
| `views/*.js` | one file per panel of the UI |

## The view contract

A view is a factory that receives a container and shared context, and returns
an object with a `render(state)` method:

```js
// static/js/views/thing.js
export function thingView(root, { api, store, player, loadMore }) {
  const render = memo(
    (state) => {
      root.innerHTML = `...`;
    },
    (state) => state.somethingThatMatters, // re-render key
  );

  return { render };
}
```

`main.js` subscribes to the store and calls `render(state)` on every view.

**Always wrap the render function in `memo()`.** Without it, audio progress
(`timeupdate`, ~4×/second) rebuilds every table in the app. The second argument
tells `memo` what this view actually depends on.

## Adding a view

1. Create `static/js/views/thing.js` following the contract above.
2. Add a container in `index.html` (`<section id="thing"></section>`).
3. In `main.js`: import it, instantiate it, push it into `views`.

That's the whole process.

## Conventions

- **Escape all API data** with `esc()` before interpolating into `innerHTML`.
  Track names come from Spotify and are untrusted.
- **Delegate events** on the container, not on individual rows — rows get
  re-rendered and would lose direct listeners.
- **Keep DOM out of state.** The store holds data; views own their DOM.
- `player.js` deliberately keeps high-frequency updates to itself and only
  notifies the store when the *track* changes.
