// Where published releases are served from.
//
// Release files (~1 GB) live in their own GitHub Pages site, repo
// Fluency-Releases, so that an app deploy republishes only the app. Config
// and artist catalogues keep naming them `releases/<language>/…`; this maps
// that name onto the release site.
//
// A local dev server that serves the app at its root keeps the relative path,
// because that is where the local speech pilot mounts workspace releases
// (docs/runbooks/local-speech-pilot.md) — unpublished releases stay testable.
// The repository preview (the shell opened at /app/) has no releases of its
// own, so it reads the published ones like production does.

export const RELEASE_BASE_URL = 'https://rabbijoshy.github.io/Fluency-Releases/';

function servesLocalReleases() {
    if (typeof window === 'undefined') return false;
    const isLocal = /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);
    return isLocal && !new URL('.', window.location.href).pathname.endsWith('/app/');
}

export function releaseUrl(path) {
    const value = String(path || '');
    if (!value.startsWith('releases/') || servesLocalReleases()) return value;
    return RELEASE_BASE_URL + value.slice('releases/'.length);
}
