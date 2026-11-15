// Blind judging: strong models from different companies score every answer in a
// bake-off run against the image itself. For each photo and prompt, the judge sees
// the image and all answers, shuffled and labelled A, B, C… with no model names.
// Several judges from different companies are averaged, so no company's bias wins.
//
//   OPENROUTER_API_KEY=... node tools/vision-bakeoff/judge.ts <results folder> [--judges a,b,c] [--photos dir]
//
// Writes judged.json into the results folder and prints summary tables.

import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, join, resolve } from 'node:path';

const HERE = import.meta.dirname;
const DEFAULT_JUDGES = ['openai/gpt-6.1-sol', 'anthropic/claude-sonnet-5.5', 'google/gemini-3.1-pro-preview'];
const CONCURRENCY = 6;

type Answer = { model: string; modelId?: string; variant?: string; photo: string; prompt: string; text: string; error: string | null };
type Score = { accuracy: number; insight: number; listening: number; completeness: number; invented: string };
const DIMS = ['accuracy', 'insight', 'listening', 'completeness'] as const;

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

const RUBRIC = (prompt: string) => `You are judging spoken image descriptions written for blind and low-vision students.
They will be read aloud by a speech engine. The ${prompt === 'describe'
  ? '"Quick look" mode asks for about 60 to 150 words: what the picture is, its mood, and the details that matter.'
  : '"Full detail" mode asks for everything a sighted classmate could study: all text read exactly (including handwriting, marks and grades), then the whole image described area by area, with mood, style and, for charts, the values.'}

Look carefully at the image, then score EVERY answer from 1 to 10 on:
- accuracy: 10 means everything stated is visibly true. Take points off for each invented or wrong detail (misread text, objects or expressions that are not there, a wrong title or artist). Misleading errors cost more.
- insight: does it capture the mood and atmosphere, and what matters most for understanding this image (the artist's or photographer's evident intent, a key expression or gesture, the purpose of a document)? Flourishes not supported by the image do not count.
- listening: natural spoken prose that is pleasant to listen to. Take points off for stock phrases and clichés ("the most striking", "draws the eye"), filler, markdown or symbols, robotic lists, and wrong length for the mode.
- completeness: Quick look: are the essentials there? Full detail: is all legible text read exactly and every part of the image covered?
Refusing, or moralising about nudity or violence instead of describing it, scores low on insight and completeness. Neutral, school-appropriate description of such content is correct.
Also list in "invented" the specific invented or wrong details you found, briefly, or "" if none.
Judge each answer on its own merits; length alone is not quality.

Reply with JSON only, in this shape:
{"scores":[{"id":"A","accuracy":0,"insight":0,"listening":0,"completeness":0,"invented":""}]}`;

function key(): string {
  const k = process.env.OPENROUTER_API_KEY?.trim();
  if (!k) throw new Error('Set OPENROUTER_API_KEY.');
  return k;
}

function photoUrl(path: string): string {
  const out = join(tmpdir(), `judge-${basename(path)}.jpg`);
  execFileSync('python3', ['-I', join(HERE, 'shrink.py'), path, out, '1568'], { stdio: ['ignore', 'ignore', 'inherit'] });
  return `data:image/jpeg;base64,${readFileSync(out).toString('base64')}`;
}

// Deterministic shuffle so a re-run shows the judge the same order.
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

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
let spent = 0; // US dollars, as reported by OpenRouter

async function judgeGroup(judge: string, image: string, prompt: string, answers: Answer[]): Promise<Record<string, Score> | string> {
  const order = shuffled(answers, `${judge}|${answers[0].photo}|${prompt}`);
  const body = order.map((a, i) => `=== Answer ${LETTERS[i]} ===\n${a.text}`).join('\n\n');
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        signal: AbortSignal.timeout(240_000),
        headers: { Authorization: `Bearer ${key()}`, 'Content-Type': 'application/json', 'X-Title': 'AllHail vision bake-off judge' },
        body: JSON.stringify({
          model: judge,
          max_tokens: 8000,
          temperature: 0,
          reasoning: { effort: 'low', exclude: true },
          provider: { data_collection: 'deny' },
          response_format: { type: 'json_object' },
          messages: [
            { role: 'system', content: RUBRIC(prompt) },
            { role: 'user', content: [{ type: 'image_url', image_url: { url: image } }, { type: 'text', text: body }] },
          ],
        }),
      });
      const b = (await res.json()) as any;
      if (!res.ok || b.error) throw new Error(`${res.status}: ${b.error?.message ?? ''}`);
      if (typeof b.usage?.cost === 'number') spent += b.usage.cost;
      const text: string = b.choices?.[0]?.message?.content ?? '';
      const json = JSON.parse(text.slice(text.indexOf('{'), text.lastIndexOf('}') + 1));
      const out: Record<string, Score> = {};
      for (const s of json.scores ?? []) {
        const a = order[LETTERS.indexOf(String(s.id).trim().toUpperCase())];
        if (a) out[a.model] = { accuracy: +s.accuracy, insight: +s.insight, listening: +s.listening, completeness: +s.completeness, invented: String(s.invented ?? '') };
      }
      if (Object.keys(out).length < order.length * 0.8) throw new Error(`only ${Object.keys(out).length}/${order.length} scored`);
      return out;
    } catch (e) {
      if (attempt === 1) return String((e as Error).message ?? e);
    }
  }
  return 'unreachable';
}

async function pool<T>(jobs: (() => Promise<T>)[], size: number): Promise<T[]> {
  const out: T[] = new Array(jobs.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(size, jobs.length) }, async () => {
    while (next < jobs.length) { const i = next++; out[i] = await jobs[i](); }
  }));
  return out;
}

const mean = (xs: number[]) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : NaN);

async function main() {
  const dir = resolve(process.argv[2] ?? '');
  const photoDir = resolve(arg('photos') ?? join(HERE, '../../sample_images'));
  const judges = (arg('judges') ?? DEFAULT_JUDGES.join(',')).split(',');
  const run = JSON.parse(readFileSync(join(dir, 'results.json'), 'utf8')) as { results: Answer[] };
  const ok = run.results.filter((r) => !r.error && r.text);

  const groups = new Map<string, Answer[]>();
  for (const r of ok) {
    const k = `${r.photo}|${r.prompt}`;
    groups.set(k, [...(groups.get(k) ?? []), r]);
  }
  const images = new Map<string, string>();
  for (const k of groups.keys()) {
    const photo = k.split('|')[0];
    if (!images.has(photo)) images.set(photo, photoUrl(join(photoDir, photo)));
  }
  console.log(`${groups.size} groups × ${judges.length} judges = ${groups.size * judges.length} judge calls`);

  // scores[judge][photo|prompt][model] = Score
  const scores: Record<string, Record<string, Record<string, Score>>> = {};
  const jobs: (() => Promise<void>)[] = [];
  for (const judge of judges) {
    scores[judge] = {};
    for (const [k, answers] of groups) {
      jobs.push(async () => {
        const [photo, prompt] = k.split('|');
        const r = await judgeGroup(judge, images.get(photo)!, prompt, answers);
        if (typeof r === 'string') console.log(`  ${judge} · ${k}: FAILED ${r.slice(0, 120)}`);
        else { scores[judge][k] = r; console.log(`  ${judge} · ${k}: ${Object.keys(r).length} scored`); }
      });
    }
  }
  await pool(jobs, CONCURRENCY);
  writeFileSync(join(dir, 'judged.json'), JSON.stringify({ judges, scores, cost: spent }, null, 2));
  console.log(`Judging cost: $${spent.toFixed(2)}`);

  // Summaries: by answer label, by prompt version, by model. Each judge's scores are
  // first averaged per label, then the judges are averaged, so each judge counts equally.
  const meta = new Map(ok.map((r) => [r.model, { modelId: r.modelId ?? r.model, variant: r.variant ?? '-' }]));
  const table = (title: string, keyOf: (label: string) => string, filter?: (prompt: string) => boolean) => {
    const acc = new Map<string, Record<string, Record<string, number[]>>>(); // key -> judge -> dim -> values
    const inv = new Map<string, { n: number; with: number }>();
    for (const judge of judges)
      for (const [k, byLabel] of Object.entries(scores[judge])) {
        if (filter && !filter(k.split('|')[1])) continue;
        for (const [label, s] of Object.entries(byLabel)) {
          const key = keyOf(label);
          const j = ((acc.get(key) ?? acc.set(key, {}).get(key)!)[judge] ??= {});
          for (const d of DIMS) (j[d] ??= []).push(s[d]);
          const v = inv.get(key) ?? { n: 0, with: 0 };
          v.n++; if (s.invented.trim()) v.with++;
          inv.set(key, v);
        }
      }
    const rows = [...acc.entries()].map(([key, byJudge]) => {
      const dim = Object.fromEntries(DIMS.map((d) => [d, mean(judges.filter((j) => byJudge[j]).map((j) => mean(byJudge[j][d])))]));
      const perJudge = judges.map((j) => (byJudge[j] ? mean(DIMS.map((d) => mean(byJudge[j][d]))) : NaN));
      const total = mean(DIMS.map((d) => dim[d]));
      const v = inv.get(key)!;
      return { key, ...dim, total, perJudge, inventedPct: (100 * v.with) / v.n };
    }).sort((a, b) => b.total - a.total);
    console.log(`\n${title}`);
    console.log(`${'name'.padEnd(44)} total  acc  ins  lis  com  invented%  ${judges.map((j) => j.split('/')[1].slice(0, 12).padStart(13)).join('')}`);
    for (const r of rows)
      console.log(`${r.key.padEnd(44)} ${r.total.toFixed(2)} ${(r as any).accuracy.toFixed(1).padStart(4)} ${(r as any).insight.toFixed(1).padStart(4)} ${(r as any).listening.toFixed(1).padStart(4)} ${(r as any).completeness.toFixed(1).padStart(4)}  ${r.inventedPct.toFixed(0).padStart(6)}%   ${r.perJudge.map((x) => x.toFixed(2).padStart(13)).join('')}`);
  };
  table('By model and prompt version (both modes)', (l) => l);
  table('By prompt version', (l) => meta.get(l)?.variant ?? '-');
  table('By model', (l) => meta.get(l)?.modelId ?? l);
  table('Quick look only, by model and version', (l) => l, (p) => p === 'describe');
  table('Full detail only, by model and version', (l) => l, (p) => p === 'detail');
}

main().catch((e) => { console.error(e.message ?? e); process.exit(1); });
