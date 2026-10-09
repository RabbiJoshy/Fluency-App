/**
 * Web Worker for Turbo Intake & WSD Pipeline.
 * Runs in the background without blocking the UI thread or Anki study timers.
 */
import { TurboEngine } from '../turbo/turbo-engine.js';

let engine = null;

self.onmessage = async (e) => {
    const { type, payload, id } = e.data;

    try {
        if (type === 'INIT') {
            const assetsUrl = payload?.assetsUrl || '../turbo/turbo_assets.json';
            engine = await TurboEngine.create(assetsUrl);
            self.postMessage({ type: 'INIT_SUCCESS', id });
        } else if (type === 'PROCESS_PLAYLIST') {
            if (!engine) {
                const assetsUrl = payload?.assetsUrl || '../turbo/turbo_assets.json';
                engine = await TurboEngine.create(assetsUrl);
            }

            const { songs, options } = payload;
            const result = await engine.processPlaylist(songs, {
                ...options,
                onProgress: (progress) => {
                    self.postMessage({
                        type: 'PROGRESS',
                        id,
                        progress
                    });
                }
            });

            self.postMessage({
                type: 'PROCESS_SUCCESS',
                id,
                result
            });
        }
    } catch (err) {
        self.postMessage({
            type: 'ERROR',
            id,
            error: err.message || String(err)
        });
    }
};
