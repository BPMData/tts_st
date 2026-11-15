# AllHail

AllHail is an installable web app for blind and low-vision students and their teachers. It will turn photos, documents and typed text into speech, alongside OverBoard, AllAboard and OverHeard.

This branch completes **step 2 of [the rebuild plan](PLAN.md)**: the project foundation. It has an accessible home screen, install instructions, connection announcements and an offline app shell. Camera capture, AI descriptions, document reading and speech come in later steps.

## Run it locally

Use **Node 24 LTS** (`nvm use` if you use nvm). Node 22.18 or later also supports the server's native TypeScript execution.

```bash
npm ci
cp .env.example .env
npm run dev
```

Open `http://localhost:3000`. No API keys are needed for this step. The development server updates the browser when you edit files. Its service worker is disabled so old cached files do not hide your edits.

To try the installable, offline version, build it and start the production server:

```bash
npm run build
NODE_ENV=production npm start
```

The server serves the built app when `NODE_ENV=production`, or when it runs on Cloud Run (which sets `K_SERVICE`), even if `NODE_ENV` is missing. `NODE_ENV=development` always means the development server.

### Deploying with Google AI Studio

- AI Studio's Publish builds the app, starts it with `node server.ts` on Cloud Run, and can rewrite the service's settings. Anything that must survive a publish belongs in code, not in console settings. That's why production is detected from `K_SERVICE` as well as `NODE_ENV`.
- Keep `PORT=3000`; don't "fix" it to 8080 (see AllAboard's deployment notes).
- `metadata.json` names the app and asks for the camera, so AI Studio's preview allows it.
- Keys go in AI Studio's **Secrets** panel, never in the code: `OPENROUTER_API_KEY` from step 3 onwards. AI Studio adds `GEMINI_API_KEY` by itself; AllHail doesn't use it.
- Test the camera and installing in the published URL in a full Chrome tab, not in AI Studio's preview pane.

`PORT` defaults to `3000`; `HOST` defaults to `0.0.0.0`. Production runs `node server.ts` directly, without a TypeScript loader. `GET /api/health` checks that the server is up. Deployment must serve over HTTPS for installation and offline support; localhost is allowed for development. A phone visiting a laptop's plain HTTP network address cannot use its service worker.

## Check changes

```bash
npm run typecheck
npm test
npm run build
node -e "import('./server.ts').then(() => console.log('OK'))"
npm run smoke
npx playwright install chromium
npm run test:pwa
```

GitHub Actions runs these checks with Node 24. Unit tests mock the service worker. The smoke test starts the production Express app on a temporary port and checks routes, cache headers, the manifest, icon sizes and the service worker. Playwright checks Chrome install eligibility and offline reopening on desktop and an emulated Android phone. It also checks that API replies are never cached. These checks do not call AI or speech services or use real photos. Test output stays ignored.

## Install and check offline on a real device

1. Open the production app over HTTPS in Chrome on a laptop or Android phone. Wait for **App saved for offline use**.
2. On a laptop, choose Chrome's install icon in the address bar. On Android, use **Install app** or **Add to Home screen** from Chrome's menu.
3. Close AllHail, disconnect from the internet, and open it again from its installed icon. Check that the home screen and install instructions open, with an offline announcement.
4. Reconnect and check that the connection announcement changes. Try keyboard navigation and large text, plus VoiceOver or TalkBack.

On iPhone or iPad, use Safari's Share menu and **Add to Home Screen**. Physical device installation and screen-reader checks still need a human; browser emulation does not replace them.

The generated worker caches only the built app files, including local icons and styles. API routes are excluded from offline navigation, and there is no runtime cache for photos, text or API results. New versions offer an **Update AllHail** button so a reload will not interrupt future work.

## Where things live

- `src/`: React app and styles (React 19, Tailwind 4).
- `shared/strings.ts`: all visible text, including HTML and manifest wording.
- `server.ts`: Express server and development Vite middleware.
- `vite.config.ts`: build, install manifest and offline cache rules.
- `public/icons/`: original SVG and install icons. Regenerate the PNGs with `node scripts/generate-icons.mjs` after installing Playwright's Chromium.
- `tools/vision-bakeoff/`: the preserved, human-run model and prompt tests. They are separate from app checks; see their [README](tools/vision-bakeoff/README.md).

Read [AGENTS.md](AGENTS.md) and [PLAN.md](PLAN.md) before changing the app. Keep API keys on the server; never use a `VITE_` variable for a secret. Personal photos, `.env` files and bake-off results stay ignored. Image preparation, tested v5 prompts and provider chains will be wired in when their features are built.

## Recover the Streamlit version

The `streamlit-final` tag preserves the complete app before its removal. To open it separately without changing this checkout:

```bash
git fetch origin tag streamlit-final
git worktree add ../allhail-streamlit streamlit-final
```

The original Python files, Streamlit configuration and requirements are all there. No personal photos or secrets are included.

Created by a high school computer science teacher to help students with vision impairments.
