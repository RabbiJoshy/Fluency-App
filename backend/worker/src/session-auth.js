import { createRemoteJWKSet, jwtVerify } from 'jose';

const keysets = new Map();
const prohibitedActions = new Set(['dump', 'lookupProfiles', 'createProfile', 'claimLegacyProfile']);

// Only the separate Clerk staging deployment opts in. Existing production
// clients and their database remain on the original worker configuration.
export async function authorizeProgress(request, params, env, verificationKeys) {
  if (!env.CLERK_ISSUER) return;
  const bearer = /^Bearer (\S+)$/.exec(request.headers.get('Authorization') || '');
  if (!bearer) throw Object.assign(new Error('Please sign in to sync your progress.'), { status: 401 });
  let payload;
  try {
    let keys = verificationKeys;
    if (!keys) {
      if (!keysets.has(env.CLERK_ISSUER)) {
        keysets.set(env.CLERK_ISSUER, createRemoteJWKSet(new URL(`${env.CLERK_ISSUER}/.well-known/jwks.json`)));
      }
      keys = keysets.get(env.CLERK_ISSUER);
    }
    ({ payload } = await jwtVerify(bearer[1], keys, {
      issuer: env.CLERK_ISSUER, algorithms: ['RS256'],
      requiredClaims: ['sub', 'exp', 'iat', 'nbf', 'sid', 'azp']
    }));
    const allowedOrigins = String(env.CLERK_ORIGIN).split(',').map(origin => origin.trim());
    if (!allowedOrigins.includes(payload.azp) || payload.sts === 'pending'
      || !/^user_[A-Za-z0-9]+$/.test(payload.sub)) throw new Error('Invalid session');
  } catch (_) {
    throw Object.assign(new Error('Your session expired. Please sign in again.'), { status: 401 });
  }
  if (prohibitedActions.has(params.action)) {
    throw Object.assign(new Error('This action is unavailable for passwordless accounts.'), { status: 403 });
  }
  const prefix = env.CLERK_ENVIRONMENT === 'production' ? '' : 'stg_';
  const expectedUser = `${prefix}clerk_${payload.sub}`;
  // Validate all supplied identities, including nested bulk rows. Never allow
  // a signed-in person to address another account by changing a request body.
  if ((params.user && params.user !== expectedUser)
    || (Array.isArray(params.rows) && params.rows.some(row => row.user && row.user !== expectedUser))) {
    throw Object.assign(new Error('This progress belongs to another account.'), { status: 403 });
  }
  params.user = expectedUser;
  if (Array.isArray(params.rows)) params.rows = params.rows.map(row => ({ ...row, user: expectedUser }));
}
