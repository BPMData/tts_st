// Vision bake-off: send every test photo to every candidate model on OpenRouter,
// record what each model said, how long it took and what it cost, and write a
// side-by-side report for scoring.
//
// Run (Node 22.18+ runs .ts files directly):
//   OPENROUTER_API_KEY=... node tools/vision-bakeoff/bakeoff.ts
// Options:
//   --photos <dir>      default tools/vision-bakeoff/photos
//   --models <file>     default tools/vision-bakeoff/models.txt (one model id per line)
//   --prompts <list>    describe,detail (default both)
//   --only <model,...>  run just these models
//   --variants v1,v2    compare prompt versions from variants.ts (default: the one in prompts.ts)
//   --reasoning off     turn "thinking" off for every model (default: low effort,
//                       or off for models marked no-thinking in models.txt)
//   --max-side N        longest side in pixels after shrinking (default 1568)
//   --only-photos a,b   test just these photos from the folder
// The key can also go in a .env file at the repo root (OPENROUTER_API_KEY=...).

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, extname, join, relative, resolve } from 'node:path';
import { CURRENT, PROMPTS, type PromptName } from './prompts.ts';
import { VARIANTS, type Prompts } from './variants.ts';
import { renderReport } from './report.ts';

const HERE = import.meta.dirname;
const ROOT = resolve(HERE, '../..');
const MAX_SIDE = Number(arg('max-side') ?? 1568); // the app shrinks photos to this before upload
const CONCURRENCY = 8;
const TIMEOUT_MS = 90_000;

export type Result = {
  model: string; // "<model id> [<variant>]" when several prompt versions are compared
  modelId: string;
  variant: string;
  retried: boolean;
  photo: string;
  prompt: PromptName;
  ms: number;
  promptTokens: number | null;
  completionTokens: number | null;
  cost: number | null; // US dollars, as reported by OpenRouter
  text: string;
  error: string | null;
};

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

function apiKey(): string {
  if (process.env.OPENROUTER_API_KEY) return process.env.OPENROUTER_API_KEY.trim();
  const envFile = join(ROOT, '.env');
  if (existsSync(envFile)) {
    const line = readFileSync(envFile, 'utf8')
      .split('\n')
      .find((l) => l.startsWith('OPENROUTER_API_KEY='));
    if (line) return line.slice('OPENROUTER_API_KEY='.length).replace(/^["']|["']$/g, '').trim();
  }
  throw new Error('Set OPENROUTER_API_KEY (environment or .env at the repo root).');
}

const MIME: Record<string, string> = {
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
  '.webp': 'image/webp', '.heic': 'image/heic',
};

/** Turn upright, shrink to MAX_SIDE and strip ALL metadata (GPS included), as the app will.
 *  If that fails the photo is not sent at all: never upload an original that may carry GPS. */
function loadPhoto(path: string): { dataUrl: string; bytes: number } {
  const out = join(tmpdir(), `bakeoff-${basename(path)}.jpg`);
  execFileSync('python3', ['-I', join(HERE, 'shrink.py'), path, out, String(MAX_SIDE)], { stdio: ['ignore', 'ignore', 'inherit'] });
  const buf = readFileSync(out);
  return { dataUrl: `data:image/jpeg;base64,${buf.toString('base64')}`, bytes: buf.length };
}

async function ask(key: string, model: string, prompts: Prompts, prompt: PromptName, dataUrl: string, noThinking: boolean): Promise<Omit<Result, 'model' | 'modelId' | 'variant' | 'retried' | 'photo' | 'prompt'>> {
  const started = performance.now();
  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      signal: AbortSignal.timeout(TIMEOUT_MS),
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
        'X-Title': 'AllHail vision bake-off',
      },
      body: JSON.stringify({
        model,
        max_tokens: 1500,
        temperature: 0.2,
        // Keep "thinking" models quick; ignored by models that don't think.
        // --reasoning off turns thinking off entirely, for models that otherwise think until they run out of room.
        reasoning: noThinking || arg('reasoning') === 'off' ? { enabled: false } : { effort: 'low', exclude: true },
        usage: { include: true },
        // Only use providers that don't keep or train on what we send (photos can show student work and names).
        provider: { data_collection: 'deny' },
        messages: [
          { role: 'system', content: prompts[prompt].system },
          {
            role: 'user',
            content: [
              { type: 'text', text: prompts[prompt].user },
              { type: 'image_url', image_url: { url: dataUrl } },
            ],
          },
        ],
      }),
    });
    const ms = Math.round(performance.now() - started);
    const body = (await res.json()) as any;
    if (!res.ok || body.error) {
      return { ms, promptTokens: null, completionTokens: null, cost: null, text: '', error: `${res.status}: ${body.error?.message ?? JSON.stringify(body).slice(0, 300)}` };
    }
    const text: string = body.choices?.[0]?.message?.content ?? '';
    return {
      ms,
      promptTokens: body.usage?.prompt_tokens ?? null,
      completionTokens: body.usage?.completion_tokens ?? null,
      cost: typeof body.usage?.cost === 'number' ? body.usage.cost : null,
      text: text.trim(),
      error: text.trim() ? null : 'Empty answer',
    };
  } catch (e) {
    return { ms: Math.round(performance.now() - started), promptTokens: null, completionTokens: null, cost: null, text: '', error: String((e as Error).message ?? e) };
  }
}

async function pool<T>(jobs: (() => Promise<T>)[], size: number): Promise<T[]> {
  const out: T[] = new Array(jobs.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(size, jobs.length) }, async () => {
      while (next < jobs.length) {
        const i = next++;
        out[i] = await jobs[i]();
      }
    })
  );
  return out;
}

async function main() {
  const key = apiKey();
  const photoDir = resolve(arg('photos') ?? join(HERE, 'photos'));
  const modelFile = resolve(arg('models') ?? join(HERE, 'models.txt'));
  const prompts = (arg('prompts') ?? 'describe,detail').split(',') as PromptName[];
  const variants = (arg('variants') ?? CURRENT).split(',').map((v) => v.trim());
  for (const v of variants) if (!VARIANTS[v]) throw new Error(`Unknown prompt version "${v}". Have: ${Object.keys(VARIANTS).join(', ')}`);
  for (const p of prompts) if (!PROMPTS[p]) throw new Error(`Unknown prompt "${p}". Use describe and/or detail.`);

  // A line is "<model id>" or "<model id> no-thinking".
  const lines = readFileSync(modelFile, 'utf8')
    .split('\n')
    .map((l) => l.replace(/#.*/, '').trim().split(/\s+/))
    .filter((parts) => parts[0]);
  const noThinking = new Set(lines.filter((p) => p.includes('no-thinking')).map((p) => p[0]));
  let models = lines.map((p) => p[0]);
  const only = arg('only');
  if (only) models = only.split(',').map((m) => m.trim());

  // --only-photos a.jpg,b.jpg: test just these photos from the folder.
  const onlyPhotos = arg('only-photos')?.split(',').map((f) => f.trim());
  const photos = readdirSync(photoDir)
    .filter((f) => MIME[extname(f).toLowerCase()])
    .filter((f) => !onlyPhotos || onlyPhotos.includes(f))
    .sort();
  if (!photos.length) throw new Error(`No photos in ${photoDir}`);
  if (onlyPhotos && photos.length < onlyPhotos.length)
    throw new Error(`Not found in ${photoDir}: ${onlyPhotos.filter((f) => !photos.includes(f)).join(', ')}`);

  const loaded = Object.fromEntries(photos.map((p) => [p, loadPhoto(join(photoDir, p))]));


  const jobs: (() => Promise<Result>)[] = [];
  for (const photo of photos)
    for (const prompt of prompts) {
      for (const model of models)
        for (const variant of variants)
          jobs.push(async () => {
            const go = () => ask(key, model, VARIANTS[variant], prompt, loaded[photo].dataUrl, noThinking.has(model));
            let r = await go();
            // A blank answer is usually a one-off glitch: retry once, and record that it happened.
            const retried = r.error === 'Empty answer';
            if (retried) r = await go();
            const label = variants.length > 1 ? `${model} [${variant}]` : model;
            const tag = r.error ? `FAILED ${r.error.slice(0, 80)}` : `${r.ms} ms, $${r.cost?.toFixed(5) ?? '?'}${retried ? ' (retried)' : ''}`;
            console.log(`  ${photo} · ${prompt} · ${label}: ${tag}`);
            return { model: label, modelId: model, variant, retried, photo, prompt, ...r };
          });
    }

  console.log(`${photos.length} photos, ${models.length} models: ${jobs.length} calls`);
  const results = await pool(jobs, CONCURRENCY);

  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const outDir = join(HERE, 'results', stamp);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, 'results.json'), JSON.stringify({ models, variants, prompts, photos, results }, null, 2));
  const labels = [...new Set(results.map((r) => r.model))];
  const thumbs = Object.fromEntries(photos.map((p) => [p, loaded[p].dataUrl]));
  // Link each original photo (relative to the report) so the page can show it full size.
  const fullSize = Object.fromEntries(
    photos.map((p) => [p, relative(outDir, join(photoDir, p)).split('/').map(encodeURIComponent).join('/')])
  );
  writeFileSync(join(outDir, 'report.html'), renderReport({ models: labels, prompts, photos, results, thumbs, fullSize }));

  const total = results.reduce((s, r) => s + (r.cost ?? 0), 0);
  console.log(`\nTotal cost: $${total.toFixed(4)}`);
  console.log(`Report: ${join(outDir, 'report.html')}`);
}

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
