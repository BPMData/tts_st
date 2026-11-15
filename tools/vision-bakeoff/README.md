# Vision bake-off

Sends every test photo to every candidate model on OpenRouter, using the app's two prompts: **Quick look** (`describe`) and **Full detail** (`detail`). It records each answer, how long it took and what it cost, and writes a side-by-side page for scoring by hand. A second script, `judge.ts`, has strong models score the answers blind.

Every photo is turned upright, shrunk and stripped of all metadata (GPS included) before upload, by `shrink.py`, the same as the app. If that step fails, the photo isn't sent. Requests go only to providers that don't keep or train on the data (`data_collection: deny`).

## Files

| File | What it is |
|---|---|
| `models.txt` | Candidate models. Add `no-thinking` after a model that otherwise thinks until it runs out of room and returns nothing (Haiku 5.5, Qwen 3.7 Flash, Gemma 4) |
| `variants.ts` | Prompt versions under test (v1–v4), built from shared parts so the differences are easy to see |
| `prompts.ts` | `CURRENT` picks the version the app uses |
| `bakeoff.ts` | Runs the models and writes `results/<time>/results.json` and `report.html` |
| `judge.ts` | Blind judging of a results folder; writes `judged.json` and prints summary tables |

## Run it

From the repo root (Node 22.18 or later runs `.ts` files directly):

```bash
OPENROUTER_API_KEY="$(cat ../openrouter.txt)" node tools/vision-bakeoff/bakeoff.ts --photos sample_images
```

Open the `report.html` it prints. Score each answer 1–5. **Hide model names** shuffles the answers so you score them blind. Scores save in the browser, and **Export scores** downloads them.

| Option | What it does |
|---|---|
| `--only a/b,c/d` | Run only these models |
| `--variants v1,v2,v3` | Compare prompt versions (default: the one in `prompts.ts`) |
| `--prompts detail` | Run only Full detail (or `describe` for Quick look) |
| `--reasoning off` | Turn thinking off for every model |
| `--photos dir` / `--models file` / `--max-side N` | Photos folder, model list, longest side after shrinking (default 1568) |

A blank answer is retried once, and the run records that it happened.

## Judge it

```bash
OPENROUTER_API_KEY="$(cat ../openrouter.txt)" node tools/vision-bakeoff/judge.ts tools/vision-bakeoff/results/<time> --photos sample_images
```

For each photo and mode, every judge sees the image and all the answers, shuffled and labelled A, B, C… with no model names. Each answer is scored 1–10 on **accuracy** (nothing invented), **insight** (mood, what matters, intent), **listening** (natural spoken prose, no stock phrases) and **completeness**, and the judge lists any invented details.

The default judges are GPT-6.1 Sol, Claude Sonnet 5.5 and Gemini 3.1 Pro. They come from three different companies, so no company's bias towards its own models wins. Change them with `--judges`.

Judging costs about $5 for 4 models × 23 photos × 2 modes. Getting the answers costs about $0.11.
