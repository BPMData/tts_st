import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp, isProduction } from '../server.ts';

// Production must be detected even when AI Studio's Publish drops NODE_ENV (Cloud Run sets K_SERVICE).
assert.equal(isProduction({ NODE_ENV: 'production' }), true);
assert.equal(isProduction({ K_SERVICE: 'allhail' }), true);
assert.equal(isProduction({ K_SERVICE: 'allhail', NODE_ENV: 'development' }), false);
assert.equal(isProduction({}), false);

// Exercise the actual built app with native Node type stripping and no API keys.
const app = await createApp({ production: true });
const server = app.listen(0, '127.0.0.1');
await once(server, 'listening');
const base = `http://127.0.0.1:${server.address().port}`;
const get = (path) => fetch(`${base}${path}`);

try {
  assert.deepEqual(await (await get('/api/health')).json(), { status: 'ok' });
  for (const path of ['/api/missing', '/api/describe']) {
    const response = await get(path);
    assert.equal(response.status, 404);
    assert.match(response.headers.get('content-type'), /application\/json/);
  }
  const home = await get('/');
  assert.equal(home.status, 200);
  assert.equal(home.headers.get('cache-control'), 'no-cache');
  const html = await home.text();
  assert.match(html, /<title>AllHail<\/title>/);
  assert.doesNotMatch(html, /%APP_/);
  assert.match(await (await get('/student')).text(), /<title>AllHail<\/title>/);
  for (const path of ['/missing.js', '/icons/missing.png']) {
    assert.equal((await get(path)).status, 404);
  }
  const script = html.match(/src="(\/assets\/[^" ]+\.js)"/)[1];
  const asset = await get(script);
  assert.match(asset.headers.get('cache-control'), /immutable/);
  assert.match(asset.headers.get('content-type'), /javascript/);
  const manifestResponse = await get('/manifest.webmanifest');
  assert.match(manifestResponse.headers.get('content-type'), /manifest\+json/);
  const manifest = await manifestResponse.json();
  assert.equal(manifest.name, 'AllHail');
  assert.equal(manifest.display, 'standalone');
  assert.equal(manifest.start_url, '/');
  assert.equal(manifest.scope, '/');
  assert.ok(manifest.icons.some((icon) => icon.sizes === '192x192'));
  assert.ok(manifest.icons.some((icon) => icon.sizes === '512x512' && icon.purpose === 'maskable'));
  for (const icon of manifest.icons) {
    const response = await get(icon.src);
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /image\/png/);
    const png = Buffer.from(await response.arrayBuffer());
    assert.equal(png.toString('hex', 0, 8), '89504e470d0a1a0a');
    assert.equal(`${png.readUInt32BE(16)}x${png.readUInt32BE(20)}`, icon.sizes);
  }
  const worker = await get('/sw.js');
  assert.equal(worker.status, 200);
  assert.equal(worker.headers.get('cache-control'), 'no-cache');
  assert.match(worker.headers.get('content-type'), /javascript/);
  console.log('Production smoke test passed: routes, assets, manifest, icons and worker.');
} finally {
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}
