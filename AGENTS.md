# AllHail: notes for AI agents (Codex, Claude, Gemini)

This repo is being rebuilt from a Streamlit app (`app.py`, `simple_2.py` and friends) into **AllHail**, an installable web app (PWA) that turns photos, documents and typed text into speech for blind and low-vision students and their teachers. It joins OverBoard, AllAboard and OverHeard.

**Read [`PLAN.md`](PLAN.md) first.** It holds every decision made so far: who the app is for, the speech fallback chain, the vision model chains for each button, the prompt tests and the build order. The **step 2** foundation is in place; start new feature work with **step 3** (Student mode). See [`README.md`](README.md) for local setup and checks. Real-device installation checks from step 2 still need a human.

## Non-negotiables

1. **Never commit photos, API keys or test results.** `sample_images/`, `tools/vision-bakeoff/photos/*`, `tools/vision-bakeoff/results/` and `.env*` are git-ignored on purpose. The test photos are the owner's personal photos. The OpenRouter key lives outside the repo and is read from `OPENROUTER_API_KEY`.
2. **Strip images before upload.** Every image is turned upright (EXIF rotation), shrunk to about 1,568 px on the longest side, and redrawn so no metadata leaves the device: no GPS, no camera details. If that fails, the image is not sent. `tools/vision-bakeoff/shrink.py` is the reference behaviour; in the app this happens in the browser (canvas).
3. **Keys stay on the server.** The browser never sees an API key. `POST /api/describe` calls OpenRouter with `provider: { data_collection: "deny" }`.
4. **Use the tested prompts.** The app's two prompts (Quick look = `describe`, Full detail = `detail`) are version **v5** in `tools/vision-bakeoff/variants.ts`, selected in `tools/vision-bakeoff/prompts.ts`. Don't reword them without re-running the bake-off (see `tools/vision-bakeoff/README.md`).
5. **Model chains** (server config, not hard-coded logic). Try the next model at once on a blank answer, an answer cut off at the length limit, a provider error, or a refusal:
   - Quick look: `anthropic/claude-haiku-5.5` (thinking off) → `google/gemini-3.5-flash-lite` → `z-ai/glm-5.3-flash`
   - Full detail: `z-ai/glm-5.3-flash` → `anthropic/claude-haiku-5.5` (thinking on) → same with thinking off → `google/gemini-3.5-flash-lite`
   - Haiku 5.5, Qwen 3.7 Flash and Gemma 4 can think until they run out of room and return nothing; send `reasoning: { enabled: false }` where the chain says "thinking off".
6. **Accessibility comes first.** It must work fully with VoiceOver and TalkBack: large targets, every control labelled, status changes announced, speech that starts automatically. The text shown on screen stays as the model wrote it. Speech gets a cleaned copy: fractions become words, and markdown and `*asterisks*` are removed.

## Stack and conventions (match the sibling apps)

- Vite + React 19 + Tailwind 4 + TypeScript in the browser; Express `server.ts` on Node.
- Production runs `node server.ts` with type stripping, so server-side code can't use `enum`, `namespace`, parameter properties or `import x = require()`. Check with `node -e "import('./server.ts').then(() => console.log('OK'))"`.
- Tests with vitest. CI on GitHub Actions runs typecheck (`tsc --noEmit`), tests, build and a server smoke test.
- `npm run dev` runs Express with Vite middleware. For install/offline checks, build first and use `NODE_ENV=production npm start`. `npm run test:pwa` checks desktop and Android-emulated Chrome; it does not replace physical-device or screen-reader checks.
- Tests never call live AI or speech services; mock them. The bake-off tools are for humans with a key and real photos, not for CI.
- All words the user sees go in one strings file so the app can be translated.
- Plain-language commit messages and docs. The owner is a teacher, not a full-time developer.
- Before removing the old Streamlit files (PLAN step 2), tag the last Streamlit commit `streamlit-final` so the old app can always be recovered.
