import { esc, memo } from '../ui.js';

/**
 * Download queue strip. Polled by main.js; this view only renders.
 */
export function downloadsView(root) {
  const render = memo(
    (state) => {
      const jobs = state.jobs;

      if (jobs.length === 0) {
        root.innerHTML = '<p class="muted small">Download queue is empty.</p>';
        return;
      }

      const running = jobs.filter((job) => job.state === 'running').length;

      root.innerHTML = `
        <div class="downloads-head">
          <h3>Downloads</h3>
          <span class="muted small">${running} running · ${jobs.length} total</span>
        </div>
        ${jobs
          .slice(0, 30)
          .map((job) => {
            const percent = Math.round((job.progress || 0) * 100);
            const error = job.error
              ? ` — <span class="failed">${esc(job.error)}</span>`
              : '';
            return `
              <div class="job">
                <div class="job-line">
                  <span class="job-name" title="${esc(job.name)}">${esc(job.name)}</span>
                  <span class="job-state ${esc(job.state)}">${esc(job.state)}</span>
                </div>
                <div class="bar"><i style="width:${percent}%"></i></div>
                <div class="job-meta muted small">${percent}%${error}</div>
              </div>`;
          })
          .join('')}`;
    },
    (state) =>
      state.jobs
        .map((job) => `${job.id}:${job.state}:${Math.round((job.progress || 0) * 100)}`)
        .join('|'),
  );

  return { render };
}
