// Bound both the connection and JSON body read, including a stalled body.
// Keep HTTP status available to callers that support a 404 fallback.
export async function readJsonWithTimeout(url, options = {}, timeoutMs = 20000) {
    const controller = new AbortController();
    let timer;
    try {
        return await Promise.race([
            (async () => {
                const response = await fetch(url, { ...options, signal: controller.signal });
                const data = response.ok ? await response.json() : null;
                return { response, data };
            })(),
            new Promise((_, reject) => {
                timer = setTimeout(() => {
                    const error = new Error('Loading took too long. Check your connection and try again.');
                    error.name = 'TimeoutError';
                    reject(error);
                    controller.abort();
                }, timeoutMs);
            }),
        ]);
    } finally {
        clearTimeout(timer);
    }
}
