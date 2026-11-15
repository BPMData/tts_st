import 'dotenv/config';
import express from 'express';
import { existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));

/**
 * Serve the built app (not the Vite dev server) when NODE_ENV says production, or when running
 * on Cloud Run (which always sets K_SERVICE). AI Studio's Publish has dropped NODE_ENV before;
 * without this, the deploy would try to start Vite, which isn't installed in production.
 * An explicit NODE_ENV=development still wins, for debugging.
 */
export function isProduction(env: NodeJS.ProcessEnv = process.env): boolean {
  if (env.NODE_ENV === 'production') return true;
  if (env.NODE_ENV === 'development') return false;
  return Boolean(env.K_SERVICE);
}

export async function createApp({ production = isProduction() } = {}) {
  const app = express();
  app.disable('x-powered-by');
  app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));
  // Unknown API routes must never return the app HTML (or be cached offline).
  app.use('/api', (_req, res) => res.status(404).json({ error: 'not_found' }));

  if (production) {
    const dist = resolve(root, 'dist');
    if (!existsSync(resolve(dist, 'index.html'))) {
      throw new Error('Build the app with npm run build before starting production.');
    }
    app.use(express.static(dist, {
      setHeaders(res, filePath) {
        // Always revalidate HTML, manifests and workers when a new build is deployed.
        res.setHeader('Cache-Control', filePath.startsWith(resolve(dist, 'assets') + '/')
          ? 'public, max-age=31536000, immutable'
          : 'no-cache');
      },
    }));
    app.get('*', (req, res, next) => {
      // Missing scripts/icons must be real 404s, never HTML with the wrong MIME type.
      if (req.path.includes('.') || !req.accepts('html')) return next();
      res.setHeader('Cache-Control', 'no-cache');
      res.sendFile(resolve(dist, 'index.html'));
    });
  } else {
    const { createServer } = await import('vite');
    const vite = await createServer({ root, server: { middlewareMode: true }, appType: 'spa' });
    app.use(vite.middlewares);
  }

  return app;
}

// Importing for checks/tests does not open a port. Production needs no TS loader.
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const app = await createApp();
  const port = Number(process.env.PORT || 3000);
  const host = process.env.HOST || '0.0.0.0';
  app.listen(port, host, () => console.log(`AllHail is listening on http://${host}:${port}`));
}
