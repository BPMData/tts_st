// Builds one HTML page for scoring a bake-off run by hand. Each photo shows every answer
// with a 1–5 score and a note box. The page starts BLIND: no model names, prompt versions,
// times or costs, and answers in shuffled order. "Reveal" shows who wrote what and the
// summary tables. Clicking a photo opens the original file full screen.
// Scores and notes save in the browser (localStorage) and export as JSON.

import type { PromptName } from './prompts.ts';

type R = {
  model: string; photo: string; prompt: PromptName; ms: number;
  promptTokens: number | null; completionTokens: number | null;
  cost: number | null; text: string; error: string | null;
};

const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// Same order every time the page is built, so a reload doesn't reshuffle.
function shuffled<T>(items: T[], seed: string): T[] {
  let h = 2166136261;
  for (const c of seed) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  const rand = () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)) >>> 0) / 2 ** 32;
  const a = [...items];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function renderReport(d: {
  models: string[]; prompts: PromptName[]; photos: string[]; results: R[];
  thumbs: Record<string, string>;
  /** Link to each original photo, relative to the report, for the full-screen viewer. */
  fullSize?: Record<string, string>;
  title?: string;
}): string {
  const data = JSON.stringify(d.results.map(({ text: _t, ...rest }) => rest));
  const sections = d.photos
    .map((photo) => {
      const blocks = d.prompts
        .map((prompt) => {
          const answers = d.results.filter((r) => r.photo === photo && r.prompt === prompt);
          const cards = shuffled(answers, `${photo}|${prompt}`)
            .map((r, i) => {
              const id = esc(`${r.photo}|${r.prompt}|${r.model}`);
              const meta = r.error
                ? `<span class="bad">failed</span>`
                : `${(r.ms / 1000).toFixed(1)} s · ${r.cost == null ? '?' : '$' + r.cost.toFixed(5)} · ${r.promptTokens ?? '?'} in / ${r.completionTokens ?? '?'} out`;
              const picker = [1, 2, 3, 4, 5]
                .map((n) => `<label><input type="radio" name="${id}" value="${n}">${n}</label>`)
                .join('');
              return `<article class="card" data-id="${id}">
  <header><b>Answer ${String.fromCharCode(65 + i)}</b> <span class="reveal"><b class="model">${esc(r.model)}</b> <small>${meta}</small></span></header>
  <p class="${r.error ? 'bad' : ''}">${esc(r.error ?? r.text)}</p>
  <div class="score">Score ${picker}</div>
  <input class="note" type="text" placeholder="Note (optional): what's right or wrong" aria-label="Note">
</article>`;
            })
            .join('\n');
          return `<h3>${prompt === 'describe' ? 'Quick look' : 'Full detail'}</h3><div class="grid">${cards}</div>`;
        })
        .join('\n');
      const full = d.fullSize?.[photo];
      const img = `<img src="${d.thumbs[photo]}" alt="${esc(photo)}">`;
      const pic = `<button type="button" class="zoom" data-full="${esc(full ?? '')}" aria-label="Show ${esc(photo)} full screen">${img}<span class="hint">Click to enlarge</span></button>`;
      return `<section><h2>${esc(photo)}</h2>${pic}${blocks}</section>`;
    })
    .join('\n');

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(d.title ?? 'AllHail vision bake-off')}</title>
<style>
:root{--bg:#f8fafc;--panel:#fff;--line:#e2e8f0;--text:#0f172a;--muted:#64748b;--accent:#0284c7;--bad:#dc2626}
@media (prefers-color-scheme:dark){:root{--bg:#090d16;--panel:#111827;--line:#1e293b;--text:#f8fafc;--muted:#94a3b8;--accent:#38bdf8;--bad:#f87171}}
body{margin:0;padding:16px;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}
main{max-width:1400px;margin:auto}
table{border-collapse:collapse;width:100%;background:var(--panel);font-variant-numeric:tabular-nums;margin:8px 0}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left}
section{margin:32px 0;border-top:2px solid var(--line)}
.zoom{all:unset;cursor:zoom-in;position:relative;display:inline-block;margin:8px 0}
.zoom img{max-width:min(100%,560px);max-height:420px;border-radius:8px;display:block}
.zoom .hint{position:absolute;right:8px;bottom:8px;background:#000a;color:#fff;font-size:12px;padding:2px 8px;border-radius:6px}
.zoom:focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:8px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;display:flex;flex-direction:column}
.card small{color:var(--muted)} .card p{flex:1;white-space:pre-wrap} .bad{color:var(--bad)}
.score label{margin-left:8px}
.note{margin-top:8px;width:100%;box-sizing:border-box;font:inherit;padding:6px 8px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--text)}
.reveal,.summary{display:none} body.revealed .reveal{display:inline} body.revealed .summary{display:block}
main>p button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font:inherit;cursor:pointer;margin-right:8px}
#viewer{position:fixed;inset:0;width:100vw;height:100vh;max-width:none;max-height:none;margin:0;padding:0;border:0;background:#000;overflow:auto}
#viewer::backdrop{background:#000}
#viewer img{display:block;max-width:100vw;max-height:100vh;margin:auto;position:absolute;inset:0;cursor:zoom-in}
#viewer.actual img{max-width:none;max-height:none;position:static;margin:0;cursor:zoom-out}
#viewer .bar{position:fixed;top:10px;right:10px;display:flex;gap:8px;z-index:1}
#viewer .bar button{font:15px system-ui,sans-serif;padding:6px 12px;border-radius:8px;border:0;background:#fffe;color:#000;cursor:pointer}
</style></head><body><main>
<h1>${esc(d.title ?? 'AllHail vision bake-off')}</h1>
<p>Score each answer 1–5 for how useful and accurate it would be to hear if you couldn't see the photo, and note anything wrong.
Model names, prompt versions, times and costs are hidden, and the answers are shuffled. Click a photo to see it full size.
Scores and notes save in this browser. When you're done, press <b>Reveal</b> to see who wrote what, then <b>Export scores</b>.</p>
<p><button id="reveal">Reveal models</button><button id="export">Export scores</button> <span id="progress"></span></p>
<div class="summary">
<h2>By answer</h2><table id="byLabel"><thead><tr><th>Model [prompt version]</th><th>Average score</th><th>Scored</th><th>Average time</th><th>Cost per 1,000 photos</th><th>Failures</th></tr></thead><tbody></tbody></table>
<h2>By prompt version</h2><table id="byVersion"><thead><tr><th>Prompt version</th><th>Average score</th><th>Scored</th></tr></thead><tbody></tbody></table>
</div>
${sections}
</main>
<dialog id="viewer" aria-label="Full-size photo">
  <div class="bar"><button type="button" id="v-size">Actual size</button><button type="button" id="v-close">Close (Esc)</button></div>
  <img alt="">
</dialog>
<script>
const RESULTS = ${data};
const KEY = 'bakeoff-scores:' + location.pathname;
let state = { scores: {}, notes: {} };
try { const s = JSON.parse(localStorage.getItem(KEY) || '{}'); state = s.scores ? s : { scores: s, notes: {} }; } catch {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch {} };
const cards = [...document.querySelectorAll('.card')];
for (const c of cards) {
  const id = c.dataset.id;
  const v = state.scores[id];
  if (v) c.querySelector('input[value="' + v + '"]').checked = true;
  c.querySelector('.score').addEventListener('change', (e) => { state.scores[id] = Number(e.target.value); save(); summary(); });
  const note = c.querySelector('.note');
  note.value = state.notes[id] || '';
  note.addEventListener('input', () => { state.notes[id] = note.value; save(); });
}
const mean = (a) => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : null);
function summary() {
  const by = {}, byV = {};
  for (const r of RESULTS) {
    const m = (by[r.model] ||= { n: 0, ms: 0, cost: 0, costN: 0, fail: 0, s: [] });
    m.n++; if (r.error) { m.fail++; continue; }
    m.ms += r.ms; if (r.cost != null) { m.cost += r.cost; m.costN++; }
    const s = state.scores[r.photo + '|' + r.prompt + '|' + r.model];
    if (s) { m.s.push(s); const v = (r.model.match(/\\[(.+)\\]$/) || [, '–'])[1]; (byV[v] ||= []).push(s); }
  }
  const rows = Object.entries(by).map(([model, m]) => ({ model, score: mean(m.s), sN: m.s.length, ms: m.n - m.fail ? m.ms / (m.n - m.fail) : null, cost: m.costN ? (m.cost / m.costN) * 1000 : null, fail: m.fail }))
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
  document.querySelector('#byLabel tbody').innerHTML = rows.map((r) =>
    '<tr><td>' + r.model + '</td><td>' + (r.score == null ? '–' : r.score.toFixed(2)) + '</td><td>' + r.sN +
    '</td><td>' + (r.ms == null ? '–' : (r.ms / 1000).toFixed(1) + ' s') + '</td><td>' + (r.cost == null ? '?' : '$' + r.cost.toFixed(2)) +
    '</td><td>' + r.fail + '</td></tr>').join('');
  document.querySelector('#byVersion tbody').innerHTML = Object.entries(byV).sort().map(([v, s]) =>
    '<tr><td>' + v + '</td><td>' + mean(s).toFixed(2) + '</td><td>' + s.length + '</td></tr>').join('');
  document.getElementById('progress').textContent = Object.keys(state.scores).length + ' of ' + cards.length + ' scored';
}
summary();
const rv = document.getElementById('reveal');
rv.onclick = () => { const on = document.body.classList.toggle('revealed'); rv.textContent = on ? 'Hide models' : 'Reveal models'; };
document.getElementById('export').onclick = () => {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' }));
  a.download = 'bakeoff-scores.json'; a.click();
};
const viewer = document.getElementById('viewer'), vimg = viewer.querySelector('img'), vsize = document.getElementById('v-size');
const setActual = (on) => { viewer.classList.toggle('actual', on); vsize.textContent = on ? 'Fit to screen' : 'Actual size'; };
document.querySelectorAll('.zoom').forEach((b) => b.addEventListener('click', () => {
  const small = b.querySelector('img').src;
  vimg.onerror = () => { vimg.onerror = null; vimg.src = small; };
  vimg.src = b.dataset.full || small; vimg.alt = b.querySelector('img').alt;
  setActual(false); viewer.showModal();
}));
vimg.onclick = vsize.onclick = () => setActual(!viewer.classList.contains('actual'));
document.getElementById('v-close').onclick = () => viewer.close();
</script></body></html>`;
}
