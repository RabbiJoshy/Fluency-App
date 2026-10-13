import assert from 'node:assert/strict';
import { generateKeyPair, SignJWT } from 'jose';
import { authorizeProgress } from '../src/session-auth.js';
import worker from '../src/index.js';

const { privateKey, publicKey } = await generateKeyPair('RS256');
const env = { CLERK_ISSUER: 'https://example.clerk.accounts.dev', CLERK_ORIGIN: 'https://fluency-staging.pages.dev' };
const now = Math.floor(Date.now() / 1000);
async function token(changes = {}) {
  return new SignJWT({ sub: 'user_abc', sid: 'sess_123', azp: env.CLERK_ORIGIN,
    iss: env.CLERK_ISSUER, iat: now, nbf: now - 1, exp: now + 60, ...changes })
    .setProtectedHeader({ alg: 'RS256' }).sign(privateKey);
}
const request = value => new Request('https://api.example/', { method: 'POST', headers: value ? { Authorization: `Bearer ${value}` } : {} });
const good = await token();
const identity = 'stg_clerk_user_abc';
const payload = { action: 'bulkSave', rows: [{ user: identity }, {}] };
await authorizeProgress(request(good), payload, env, publicKey);
assert.equal(payload.user, identity);
assert(payload.rows.every(row => row.user === identity));
const productionTrial = { action: 'capabilities' };
await authorizeProgress(request(await token({ azp: 'https://rabbijoshy.github.io' })), productionTrial,
  { ...env, CLERK_ORIGIN: `${env.CLERK_ORIGIN},https://rabbijoshy.github.io` }, publicKey);
assert.equal(productionTrial.user, identity);
for (const bad of [null, good.slice(0, -8) + 'tampered', await token({ exp: now - 1 }),
  await token({ nbf: now + 60 }), await token({ iss: 'https://other.clerk.accounts.dev' }),
  await token({ azp: 'https://attacker.example' }), await token({ sts: 'pending' }),
  await token({ sub: 'JST' }), await token({ azp: undefined })]) {
  await assert.rejects(authorizeProgress(request(bad), { action: 'load' }, env, publicKey), error => error.status === 401);
}
for (const params of [{ action: 'load', user: 'stg_clerk_user_other' },
  { action: 'bulkSave', rows: [{ user: 'JST' }] }, { action: 'dump' }, { action: 'lookupProfiles' }]) {
  await assert.rejects(authorizeProgress(request(good), params, env, publicKey), error => error.status === 403);
}
await authorizeProgress(request(null), { action: 'load', user: 'JST' }, {});
let dbAccess = false;
const anonymous = await worker.fetch(new Request('https://api.example/', {
  method: 'POST', body: JSON.stringify({ action: 'load', user: identity })
}), { ...env, DB: { prepare() { dbAccess = true; throw new Error('Unexpected access'); } } });
assert.equal(anonymous.status, 401);
assert.equal(dbAccess, false);
const preflight = await worker.fetch(new Request('https://api.example/', { method: 'OPTIONS' }), env);
assert(preflight.headers.get('Access-Control-Allow-Headers').includes('Authorization'));

// The frontend transport must never send Clerk credentials to Spotify,
// static assets, the legacy production API, or arbitrary third-party URLs.
globalThis.window = { __FLUENCY_ENV__: 'production', location: { hostname: 'example.com', href: 'https://example.com/' } };
const { authenticatedSyncFetch } = await import('../../../app/js/passwordless-auth.js');
let seen, tokenCalls = 0;
const nativeFetch = async (...args) => { seen = args; return new Response('{}'); };
const endpoint = 'https://auth-staging.example/';
const transport = authenticatedSyncFetch(nativeFetch, () => ({ getToken: async () => { tokenCalls++; return 'test-token'; } }), endpoint);
await transport('https://spotify.example/', { headers: { 'X-Test': 'kept' } });
assert.equal(tokenCalls, 0);
assert.equal(seen[1].headers['X-Test'], 'kept');
await transport(endpoint, { headers: { 'X-Test': 'kept' }, method: 'POST', body: '{}' });
assert.equal(seen[1].headers.get('Authorization'), 'Bearer test-token');
assert.equal(seen[1].headers.get('X-Test'), 'kept');
assert.equal(seen[1].body, '{}');
await assert.rejects(authenticatedSyncFetch(nativeFetch, () => null, endpoint)(endpoint), error => error.auth === true);
console.log('Passwordless ownership, token validation, legacy compatibility and transport isolation passed.');
