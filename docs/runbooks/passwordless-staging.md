# Passwordless staging

Staging uses the Fluency Clerk development instance, Google sign-in and email
verification codes. Password creation is disabled. Production still uses the
existing profiles and backend.

The staging frontend key is public. Neither the frontend nor worker needs a
Clerk secret key: `jose` checks session signatures against the instance's public
JWKS, issuer, expiry, activation time and the staging origin. All progress
identities, including bulk rows, must belong to the authenticated Clerk user.
Profile-directory and database-dump actions are unavailable in this deployment.

The dedicated `fluency-auth-staging` worker uses its own D1 database. These
accounts begin with empty staging progress; existing production or legacy
profiles are not automatically linked. Do not use a matching email or display
name as evidence of ownership of a legacy profile.

## Deploy

```
npm ci --prefix backend/worker
npx wrangler d1 migrations apply fluency-auth-staging --remote --config backend/worker/wrangler.auth-staging.toml
npx wrangler deploy --config backend/worker/wrangler.auth-staging.toml
make stage
```

## Review

Sign up on staging with Google or an actual email code. Study a card, wait for
sync, then sign in with the same account on another device and check progress.
Check that refresh remembers the account, logout returns to sign-in, and
unauthenticated requests cannot read or modify progress.

Clerk development branding and shared Google credentials are intentional for
this review. A production instance, production Google credentials, production
origin/key configuration and a deliberate legacy-account migration plan are
needed before enabling this in production.
