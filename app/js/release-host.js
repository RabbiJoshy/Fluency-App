// Where published releases are served from.
//
// Each first path segment has its own GitHub Pages site: `releases/<segment>/…`
// is served from repo Fluency-Releases-<segment> (es, pt, cs, fi, fr, lyrics),
// so publishing one language rebuilds only that language's site and an app
// deploy republishes only the app (docs/decisions/0026). Config and artist
// catalogues keep naming files `releases/<segment>/…`; this maps that name
// onto the segment's site. A new language needs a new repository, not an edit
// here.
//
// A local dev server that serves the app at its root keeps the relative path,
// because that is where the local speech pilot mounts workspace releases
// (docs/runbooks/local-speech-pilot.md) — unpublished releases stay testable.
// The repository preview (the shell opened at /app/) has no releases of its
// own, so it reads the published ones like production does.

export const RELEASE_SITE_ROOT = 'https://rabbijoshy.github.io/';

function servesLocalReleases() {
    if (typeof window === 'undefined') return false;
    const isLocal = /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);
    return isLocal && !new URL('.', window.location.href).pathname.endsWith('/app/');
}

export function releaseUrl(path) {
    const value = String(path || '');
    if (!value.startsWith('releases/') || servesLocalReleases()) return value;
    const rest = value.slice('releases/'.length);
    const slash = rest.indexOf('/');
    if (slash <= 0) return value;
    return `${RELEASE_SITE_ROOT}Fluency-Releases-${rest.slice(0, slash)}/${rest.slice(slash + 1)}`;
}
