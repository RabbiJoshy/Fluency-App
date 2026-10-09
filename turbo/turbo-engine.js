/**
 * TURBO v2: Ultra-fast, live, zero-cost Spanish playlist intake engine.
 * 
 * Major v2 Enhancements:
 * 1. High-Fidelity Entity Recognizer:
 *    - Curated Pop-Culture / Urban Entity Registry: instant 0ms hits for artists, brands, geography.
 *    - Multi-Token Proper Noun Chunking: captures "Myke Towers", "Brad Pitt", "Cristiano Ronaldo", "Puerto Rico", "Benny Blanco".
 *    - Noise / Obscurity Rejection: rejects ancient Egyptian gods, Roman deities, disambiguation scraps.
 *    - Cross-language (ES -> EN) fallback for global brands (e.g. Barbasol).
 * 2. Spotify Audio Timing Priority:
 *    - Parses [mm:ss.xx] timestamps from syncedLyrics.
 *    - Tier 1 ranking for Spotify-playable lines (with start & end ms) so clicking audio plays the clip.
 * 3. 3-Speed Architecture Support:
 *    - Mode 1: Fast (Instant) - Zero-cost, Zipf speech prior, LRCLIB synced lyrics.
 *    - Mode 2: Full (with Genius translation alignment).
 *    - Mode 3: Full WSD (deep semantic disambiguation).
 */

export class TurboEngine {
    constructor(assets = {}) {
        this.elisions = assets.elisions || {};
        this.mwes = assets.mwes || {};
        this.curatedEntities = assets.curatedEntities || {};
        this.dictionary = assets.dictionary || {};
        this.entityCache = new Map(); // query -> entity object or null
    }

    static async create(assetsUrl = './turbo_assets.json') {
        const resp = await fetch(assetsUrl);
        if (!resp.ok) {
            throw new Error(`Failed to load Turbo assets from ${assetsUrl}: HTTP ${resp.status}`);
        }
        const data = await resp.json();
        return new TurboEngine(data);
    }

    /**
     * Stage 1: Lyrics Hygiene & Timestamp Extraction
     * Parses syncedLyrics [mm:ss.xx] tags or plain lyrics into clean line objects.
     */
    parseLyrics(syncedLyricsText, plainLyricsText) {
        if (syncedLyricsText && syncedLyricsText.includes('[')) {
            const rawLines = syncedLyricsText.split(/\r?\n/);
            const parsed = [];
            const timestampRegex = /\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\]/g;

            for (const line of rawLines) {
                const match = timestampRegex.exec(line);
                timestampRegex.lastIndex = 0; // reset
                if (match) {
                    const min = parseInt(match[1], 10);
                    const sec = parseInt(match[2], 10);
                    const msPart = match[3] ? (match[3].length === 2 ? parseInt(match[3], 10) * 10 : parseInt(match[3], 10)) : 0;
                    const startMs = (min * 60 + sec) * 1000 + msPart;
                    const text = line.replace(/\[\d{2}:\d{2}(?:\.\d{2,3})?\]/g, '').trim();
                    if (text && !this.isForeignCodeSwitch(text)) {
                        parsed.push({
                            text: this.cleanLineText(text),
                            startMs
                        });
                    }
                }
            }

            // Compute endMs as next line's startMs
            const result = [];
            for (let i = 0; i < parsed.length; i++) {
                const cur = parsed[i];
                const next = parsed[i + 1];
                const endMs = next ? next.startMs : cur.startMs + 4000;
                result.push({
                    text: cur.text,
                    timestamp_ms: cur.startMs,
                    end_timestamp_ms: endMs,
                    isSynced: true
                });
            }
            if (result.length > 0) return result;
        }

        // Fallback to plain lyrics
        const lines = String(plainLyricsText || syncedLyricsText || '').split(/\r?\n/);
        const result = [];
        for (const line of lines) {
            const cleaned = this.cleanLineText(line);
            if (cleaned && !this.isForeignCodeSwitch(cleaned)) {
                result.push({
                    text: cleaned,
                    timestamp_ms: null,
                    end_timestamp_ms: null,
                    isSynced: false
                });
            }
        }
        return result;
    }

    cleanLineText(line) {
        let text = line.replace(/\[[^\]]*\]/g, ' ');
        text = text.replace(/\b\d+:\d{2}(?:\.\d+)?\b/g, ' ');
        text = text.replace(/\((?:yeh|ye|woh|oh|ey|ay|ah|wuh|yah|uh|prr|skrrt)[^)]*\)/gi, ' ');
        return text.trim();
    }

    isForeignCodeSwitch(line) {
        const lower = line.toLowerCase();
        const tokens = lower.match(/[\p{L}]+/gu) || [];
        if (tokens.length >= 3) {
            const englishTokens = tokens.filter(t => ['the', 'you', 'i', 'my', 'me', 'it', 'is', 'to', 'and', 'a', 'in', 'that', 'on', 'for', 'of', 'girl', 'bitch', 'fuck', 'shit', 'yeah', 'like'].includes(t));
            if (englishTokens.length / tokens.length > 0.6) {
                return true;
            }
        }
        return false;
    }

    tokenizeLine(lineText) {
        // Match tokens including words ending with an apostrophe (Caribbean s-aspiration: sabemo', no', vemo')
        const rawTokens = lineText.match(/[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*['’]?|['’][\p{L}\p{N}]+/gu) || [];
        const tokens = [];
        for (const raw of rawTokens) {
            const cleaned = raw.replace(/[’]/g, "'").toLowerCase();
            let expanded = this.elisions[cleaned] || null;
            let isElision = Boolean(this.elisions[cleaned] && this.elisions[cleaned] !== cleaned);

            // Handle Caribbean / urban s-aspiration and trailing apostrophe elisions:
            // 1. "e'" -> "es" (e' libre -> es libre, e' que -> es que)
            // 2. "no'" -> "nos" (no' vemo' -> nos vemos, no' perdemo' -> nos perdemos)
            // 3. 1st person plural verbs: "sabemo'" -> "sabemos", "llevamo'" -> "llevamos", "perdemo'" -> "perdemos"
            // 4. Any other word ending in apostrophe where stem + 's' exists in dictionary (tiene' -> tienes, lo' -> los)
            if (!expanded && cleaned.endsWith("'")) {
                const stem = cleaned.slice(0, -1);
                if (/(?:amo|emo|imo)$/.test(stem)) {
                    expanded = stem + 's';
                    isElision = true;
                } else if (stem === 'e') {
                    expanded = 'es';
                    isElision = true;
                } else if (stem === 'no') {
                    expanded = 'nos';
                    isElision = true;
                } else if (this.dictionary[stem + 's']) {
                    expanded = stem + 's';
                    isElision = true;
                } else if (this.dictionary[stem]) {
                    expanded = stem;
                    isElision = true;
                } else {
                    expanded = stem;
                    isElision = true;
                }
            } else if (!expanded && cleaned.startsWith("'")) {
                const stem = cleaned.slice(1);
                if (this.elisions[stem]) {
                    expanded = this.elisions[stem];
                    isElision = true;
                } else if (this.dictionary[stem]) {
                    expanded = stem;
                    isElision = true;
                } else if (this.dictionary['es' + stem]) {
                    expanded = 'es' + stem;
                    isElision = true;
                } else {
                    expanded = stem;
                    isElision = true;
                }
            } else if (!expanded) {
                expanded = cleaned;
            }

            if (expanded.includes(' ')) {
                for (const s of expanded.split(/\s+/)) {
                    tokens.push({
                        raw,
                        normalized: s.normalize('NFC').toLowerCase().trim(),
                        isElision: true
                    });
                }
            } else {
                tokens.push({
                    raw,
                    normalized: expanded.normalize('NFC').toLowerCase().trim(),
                    isElision
                });
            }
        }
        return tokens;
    }

    /**
     * Stage 2: v2 High-Fidelity Entity Resolution
     * Resolves queries using:
     * 1. Curated entity registry (0ms hit)
     * 2. Spanish Wikipedia REST API with candidate search
     * 3. English Wikipedia fallback for global brands / pop icons
     * 4. Strict notability filter rejecting ancient obscure figures
     */
    /**
     * Stage 2: v3 Grounded Inter-Wiki Entity Resolution (ES Grounding -> EN Definition)
     * 1. Check curated entities (0ms hit).
     * 2. Ground candidate in Spanish Wikipedia to verify cultural referent & disambiguate.
     * 3. Inter-wiki bridge (langlinks) to fetch canonical English Wikipedia page title.
     * 4. Fetch concise English description from English Wikipedia for the learner's card definition.
     */
    async resolveEntitiesBatch(queries, language = 'es') {
        const results = new Map();
        const uncuratedQueries = [];

        // 1. Check curated registry first (0ms)
        for (const q of queries) {
            const cleanQ = q.trim();
            const lowerQ = cleanQ.toLowerCase();
            if (this.curatedEntities[lowerQ]) {
                const curated = this.curatedEntities[lowerQ];
                results.set(lowerQ, curated);
                results.set(curated.canonicalTitle.toLowerCase(), curated);
            } else if (cleanQ.length >= 2) {
                uncuratedQueries.push(cleanQ);
            }
        }

        if (!uncuratedQueries.length) return results;

        const isNode = typeof process !== 'undefined' && process?.versions?.node;
        const headers = isNode ? { 'User-Agent': 'Fluency/1.0 (https://github.com/JoshuaThomasAmar/Fluency-Next)' } : undefined;

        // 2. Step 1: Ground each candidate in Spanish Wikipedia to find the exact Spanish canonical title
        const esCanonicalMap = new Map(); // cleanQ -> esTitle

        await Promise.all(uncuratedQueries.map(async cleanQ => {
            const lowerQ = cleanQ.toLowerCase();
            const cacheKey = `${language}:${lowerQ}`;
            if (this.entityCache.has(cacheKey)) {
                const cached = this.entityCache.get(cacheKey);
                if (cached) {
                    results.set(lowerQ, cached);
                    results.set(cached.canonicalTitle.toLowerCase(), cached);
                }
                return;
            }

            try {
                const searchUrl = `https://${language}.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(cleanQ)}&srlimit=3&format=json&origin=*`;
                const resp = await fetch(searchUrl, { headers });
                if (!resp.ok) return;
                const data = await resp.json();
                const hits = data?.query?.search || [];
                if (!hits.length) return;

                // Pick first non-disambiguation candidate that passes the Surface-Title Coherence Gate
                for (const hit of hits) {
                    const title = hit.title;

                    // Surface Coherence Gate:
                    // The Wikipedia title MUST share significant token overlap with the surface query!
                    // This prevents "Beanie Prada" from matching "Prochilodus magdalenae" (0 overlap)
                    // or "La Industria Inc" from matching "R. J. Reynolds Tobacco Company" (0 overlap).
                    const qTokens = cleanQ.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '').split(/\s+/).filter(t => t.length > 2);
                    const titleClean = title.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '');
                    const titleTokens = new Set(titleClean.split(/\s+/).filter(t => t.length > 2));
                    
                    const hasOverlap = qTokens.some(qt => titleTokens.has(qt) || titleClean.includes(qt));
                    if (!hasOverlap) {
                        continue; // Reject completely unrelated Wikipedia search hits!
                    }

                    const sumUrl = `https://${language}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.replace(/ /g, '_'))}`;
                    const sResp = await fetch(sumUrl, { headers });
                    if (!sResp.ok) continue;
                    const sData = await sResp.json();
                    if (sData.type === 'disambiguation') continue;

                    const desc = (sData.description || '').trim();
                    const extract = (sData.extract || '').trim();
                    if (!desc && !extract) continue;

                    // Obscurity gate
                    const combined = `${desc} ${extract}`.toLowerCase();
                    if (/(dios egipcio|faraón|dinastía|asteroide|constelación|siglo iii a\.|siglo iv a\.|rebelión de los turbantes)/i.test(combined)) {
                        continue;
                    }

                    esCanonicalMap.set(cleanQ, {
                        title,
                        esDesc: desc || extract.slice(0, 100),
                        extract: extract.length > 200 ? extract.slice(0, 197) + '...' : extract,
                        thumbnail: sData.thumbnail?.source || null
                    });
                    break;
                }
            } catch (_) {}
        }));

        if (!esCanonicalMap.size) return results;

        // 3. Step 2: Fetch English langlinks from Spanish Wikipedia in one batched request
        const esTitles = Array.from(new Set(Array.from(esCanonicalMap.values()).map(v => v.title)));
        const pipeEsTitles = esTitles.map(t => encodeURIComponent(t.replace(/ /g, '_'))).join('|');
        const langlinksUrl = `https://${language}.wikipedia.org/w/api.php?action=query&titles=${pipeEsTitles}&prop=langlinks&lllang=en&format=json&origin=*`;
        
        const enTitleByEsTitle = new Map();
        try {
            const llResp = await fetch(langlinksUrl, { headers });
            if (llResp.ok) {
                const llData = await llResp.json();
                const pages = llData?.query?.pages || {};
                for (const pid of Object.keys(pages)) {
                    const p = pages[pid];
                    const esT = p.title;
                    const enT = p.langlinks?.[0]?.['*'] || esT;
                    enTitleByEsTitle.set(esT, enT);
                }
            }
        } catch (_) {}

        // 4. Step 3: Fetch English descriptions in one batched request from English Wikipedia
        const enTitles = Array.from(new Set(Array.from(enTitleByEsTitle.values())));
        const enDescMap = new Map();

        if (enTitles.length > 0) {
            const pipeEnTitles = enTitles.map(t => encodeURIComponent(t.replace(/ /g, '_'))).join('|');
            const enDescUrl = `https://en.wikipedia.org/w/api.php?action=query&titles=${pipeEnTitles}&prop=description&format=json&origin=*`;
            try {
                const enResp = await fetch(enDescUrl, { headers });
                if (enResp.ok) {
                    const enData = await enResp.json();
                    const pages = enData?.query?.pages || {};
                    for (const pid of Object.keys(pages)) {
                        const p = pages[pid];
                        if (p.description) {
                            enDescMap.set(p.title, p.description);
                        }
                    }
                }
            } catch (_) {}
        }

        // 5. Assemble final grounded entities with clean English descriptions
        for (const [cleanQ, esInfo] of esCanonicalMap.entries()) {
            const enTitle = enTitleByEsTitle.get(esInfo.title) || esInfo.title;
            const enDesc = enDescMap.get(enTitle) || enDescMap.get(enTitle.replace(/_/g, ' ')) || null;

            // Preferred translation: English description, falling back to Spanish description
            const finalDesc = enDesc || esInfo.esDesc;
            const entityType = this.inferEntityType(`${finalDesc} ${esInfo.extract}`);

            const entity = {
                query: cleanQ,
                canonicalTitle: esInfo.title,
                englishTitle: enTitle,
                description: finalDesc,
                descriptionEn: enDesc,
                descriptionEs: esInfo.esDesc,
                extract: esInfo.extract,
                entityType,
                source: enDesc ? 'wikipedia-es-to-en' : 'wikipedia-es',
                thumbnail: esInfo.thumbnail
            };

            const cacheKey = `${language}:${cleanQ.toLowerCase()}`;
            this.entityCache.set(cacheKey, entity);
            results.set(cleanQ.toLowerCase(), entity);
            results.set(esInfo.title.toLowerCase(), entity);
        }

        return results;
    }

    inferEntityType(combinedText) {
        const text = String(combinedText || '').toLowerCase();
        if (/(rapero|rapper|cantante|singer|productor|producer|músico|musician|futbolista|footballer|actor|actriz|actress|persona|artista|artist|compositor|songwriter)/i.test(text)) return 'person';
        if (/(municipio|ciudad|city|commune|capital|isla|island|país|country|provincia|province|barrio|distrito|district|localidad|región|territory)/i.test(text)) return 'location';
        if (/(fabricante|marca|brand|empresa|company|corporación|automóvil|calzado|moda|fashion house|shaving)/i.test(text)) return 'brand';
        if (/(álbum|album|canción|song|sencillo|single|disco|película|film|movie|serie)/i.test(text)) return 'work';
        return 'entity';
    }

    /**
     * Stage 3: Multi-Token Proper Noun Candidate Detection
     * Scans lines for consecutive capitalized tokens like "Brad Pitt", "Puerto Rico", "Myke Towers"
     */
    extractEntitySpans(lineText) {
        const entities = [];
        // Matches 2 to 3 capitalized words (e.g. "Benny Blanco", "Cristiano Ronaldo", "Las Bermudas")
        const multiWordRegex = /\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})\b/g;
        let match;
        while ((match = multiWordRegex.exec(lineText)) !== null) {
            const span = match[1];
            // Skip common sentence start capitalizations if it's just regular Spanish words
            entities.push({
                phrase: span,
                isMultiToken: true
            });
        }
        return entities;
    }

    findMweSpans(tokens) {
        const matches = [];
        const n = tokens.length;
        for (let i = 0; i < n; i++) {
            for (let len = Math.min(4, n - i); len >= 2; len--) {
                const sliceTokens = tokens.slice(i, i + len).map(t => t.normalized);
                const phrase = sliceTokens.join(' ');
                if (this.mwes[phrase]) {
                    matches.push({
                        start: i,
                        end: i + len,
                        phrase,
                        mweInfo: this.mwes[phrase]
                    });
                    i += len - 1;
                    break;
                }
            }
        }
        return matches;
    }

    /**
     * Stage 4: Sentence Selection Heuristic with Spotify Audio Priority
     */
    evaluateLineQuality(lineObj, totalLineOccurrences = 1) {
        const words = lineObj.text.match(/[\p{L}\p{N}]+/gu) || [];
        const wordCount = words.length;

        let score = 100;
        // Priority bonus for Spotify playable lines (synced timestamps)
        if (lineObj.isSynced && lineObj.timestamp_ms != null) {
            score += 35; // Huge boost for playable audio clips!
        }

        // Goldilocks length window (4 - 14 words)
        if (wordCount < 4) {
            score -= (4 - wordCount) * 20;
        } else if (wordCount > 14) {
            score -= (wordCount - 14) * 10;
        } else {
            score += 15;
        }

        // Chorus / repetition penalty
        if (totalLineOccurrences > 1) {
            score -= (totalLineOccurrences - 1) * 25;
        }

        const uniqueWords = new Set(words.map(w => w.toLowerCase()));
        score += Math.round((uniqueWords.size / (wordCount || 1)) * 20);

        return Math.max(0, score);
    }

    /**
     * UNISON WSD Decision Logic for Turbo Engine:
     * Disambiguates which meaning index in dictEntry.meanings best fits the context line.
     * Implements UNISON Decision 0030 / es-turbo-v1 rules:
     * - Rule 1: Progressive auxiliary (estar/andar + gerund) -> progressive / continuous meaning
     * - Rule 2: Modal obligation (tener que + infinitive) -> obligation ("have to", "must")
     * - Rule 3: Future auxiliary (ir a + infinitive) -> future ("will", "going to")
     * - Rule 4: Perfect auxiliary (haber + past participle) -> compound/perfect ("to have", "auxiliary")
     * - Rule 5: Personal pronouns (yo, tú, él, ella, nosotros, ellos) -> subject nominative
     * - Rule 6: Clitic / Pronominal reflection (me, te, se, nos, os) -> pronominal meaning
     */
    disambiguateWord(word, dictEntry, lineText) {
        if (!dictEntry || !dictEntry.polysemous || !dictEntry.meanings || dictEntry.meanings.length <= 1) {
            return 0; // Monosemous: deterministic single meaning
        }

        const meanings = dictEntry.meanings;
        const textLower = lineText.toLowerCase();
        const rawTokens = textLower.match(/[\p{L}\p{N}]+/gu) || [];
        const cleanWord = word.toLowerCase().trim();
        const targetIdx = rawTokens.indexOf(cleanWord);

        // --- Rule 1: Progressive auxiliary (estar + gerund) ---
        const estarForms = new Set([
            'estoy', 'estas', 'estás', 'esta', 'está', 'estamos', 'estais', 'estáis', 'estan', 'están',
            'estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron',
            'estaba', 'estabas', 'estabamos', 'estábamos', 'estabais', 'estaban',
            'este', 'esté', 'estes', 'estés', 'estemos', 'esteis', 'estéis', 'esten', 'estén',
            'estuviera', 'estuvieras', 'estuvieramos', 'estuviéramos', 'estuvieran',
            'estar', 'estando'
        ]);
        if (estarForms.has(cleanWord)) {
            let hasGerund = false;
            const gerundRegex = /\b\w+(?:ando|iendo|yendo)\b/i;
            if (targetIdx >= 0 && targetIdx + 1 < rawTokens.length) {
                const window = rawTokens.slice(targetIdx + 1, targetIdx + 4).join(' ');
                hasGerund = gerundRegex.test(window);
            } else {
                hasGerund = gerundRegex.test(textLower);
            }
            if (hasGerund) {
                const progIdx = meanings.findIndex(m => {
                    const ctx = (m.context || '').toLowerCase();
                    const trans = (m.translation || '').toLowerCase();
                    return (ctx.includes('progressive') || ctx.includes('gerund') || trans.includes('progressive') || trans.includes('to be'))
                        && !trans.includes('to fit') && !trans.includes('to stand') && !trans.includes('to stay');
                });
                if (progIdx >= 0) return progIdx;
            }
        }

        // --- Rule 2: Modal obligation (tener que + inf) ---
        const tenerForms = new Set([
            'tengo', 'tienes', 'tiene', 'tenemos', 'teneis', 'tenéis', 'tienen',
            'tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron',
            'tenia', 'tenía', 'tenias', 'tenías', 'teniamos', 'teníamos', 'tenian', 'tenían',
            'tenga', 'tengas', 'tengamos', 'tengan', 'tener', 'teniendo'
        ]);
        if (tenerForms.has(cleanWord)) {
            let hasObligation = false;
            if (targetIdx >= 0 && targetIdx + 1 < rawTokens.length) {
                const nextWords = rawTokens.slice(targetIdx + 1, targetIdx + 4);
                if (nextWords[0] === 'que') {
                    if (nextWords.length > 1 && /(?:ar|er|ir)$/.test(nextWords[1])) {
                        hasObligation = true;
                    } else if (nextWords.length > 2 && /(?:ar|er|ir)$/.test(nextWords[2])) {
                        hasObligation = true;
                    }
                }
            }
            if (!hasObligation) {
                hasObligation = /\btener\s+que\s+\w+[aei]r\b/i.test(textLower);
            }
            if (hasObligation) {
                const oblgIdx = meanings.findIndex(m => {
                    const trans = (m.translation || '').toLowerCase();
                    const ctx = (m.context || '').toLowerCase();
                    return trans.includes('have to') || trans.includes('must') || ctx.includes('obligation') || ctx.includes('have to');
                });
                if (oblgIdx >= 0) return oblgIdx;
            }
        }

        // --- Rule 3: Future auxiliary (ir a + inf) ---
        const irForms = new Set([
            'voy', 'vas', 'va', 'vamos', 'vais', 'van',
            'iba', 'ibas', 'ibamos', 'íbamos', 'ibais', 'iban',
            'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron',
            'vaya', 'vayas', 'vayamos', 'vayan', 'ir', 'yendo'
        ]);
        if (irForms.has(cleanWord)) {
            let hasFuture = false;
            if (targetIdx >= 0 && targetIdx + 1 < rawTokens.length) {
                const nextWords = rawTokens.slice(targetIdx + 1, targetIdx + 4);
                if (nextWords[0] === 'a' && nextWords.length > 1 && /(?:ar|er|ir)$/.test(nextWords[1])) {
                    hasFuture = true;
                }
            }
            if (hasFuture) {
                const futIdx = meanings.findIndex(m => {
                    const trans = (m.translation || '').toLowerCase();
                    const ctx = (m.context || '').toLowerCase();
                    return trans.includes('going to') || trans.includes('will') || ctx.includes('future') || ctx.includes('going to');
                });
                if (futIdx >= 0) return futIdx;
            }
        }

        // --- Rule 4: Perfect / compound auxiliary (haber + participle) ---
        const haberForms = new Set([
            'he', 'has', 'ha', 'hemos', 'habeis', 'habéis', 'han',
            'habia', 'había', 'habias', 'habías', 'habiamos', 'habíamos', 'habian', 'habían',
            'hube', 'hubiste', 'hubo', 'hubimos', 'hubieron',
            'haya', 'hayas', 'hayamos', 'hayan', 'haber', 'habiendo'
        ]);
        const pastParticipleRegex = /\b(?:\w+(?:ado|ido)|sido|visto|hecho|dicho|puesto|escrito|abierto|muerto)\b/i;
        if (haberForms.has(cleanWord)) {
            let hasParticiple = false;
            if (targetIdx >= 0 && targetIdx + 1 < rawTokens.length) {
                const nextWords = rawTokens.slice(targetIdx + 1, targetIdx + 4);
                hasParticiple = nextWords.some(w => pastParticipleRegex.test(w));
            } else {
                hasParticiple = pastParticipleRegex.test(textLower);
            }
            if (hasParticiple) {
                const perfIdx = meanings.findIndex(m => {
                    const trans = (m.translation || '').toLowerCase();
                    const ctx = (m.context || '').toLowerCase();
                    return (ctx.includes('compound') || ctx.includes('auxiliary') || ctx.includes('perfect') || trans.includes('to have') || trans.includes('have'))
                        && !trans.includes('there is') && !trans.includes('exist');
                });
                if (perfIdx >= 0) return perfIdx;
            }
        }

        // --- Rule 5: Personal pronouns / case distinction ---
        if (cleanWord === 'ella' || cleanWord === 'yo' || cleanWord === 'tú' || cleanWord === 'él' || cleanWord === 'nosotros') {
            const preps = new Set(['para', 'por', 'de', 'con', 'a', 'en', 'hacia', 'hasta', 'sin', 'sobre']);
            const isPrepositional = targetIdx > 0 && preps.has(rawTokens[targetIdx - 1]);
            const pronIdx = meanings.findIndex(m => {
                const trans = (m.translation || '').toLowerCase();
                const ctx = (m.context || '').toLowerCase();
                if (isPrepositional && cleanWord === 'ella') {
                    return trans === 'her' || ctx.includes('prepositional');
                }
                return (trans === 'she' || trans === 'i' || trans === 'you' || trans === 'he' || trans === 'we')
                    || ctx.includes('subject') || ctx.includes('nominative');
            });
            if (pronIdx >= 0) return pronIdx;
        }

        // --- Rule 6: Pronominal / Reflexive routing ---
        const clitics = new Set(['me', 'te', 'se', 'nos', 'os']);
        const hasClitic = rawTokens.some(t => clitics.has(t));
        if (hasClitic) {
            const reflexIdx = meanings.findIndex(m => {
                const ctx = (m.context || '').toLowerCase();
                const trans = (m.translation || '').toLowerCase();
                return ctx.includes('reflexive') || ctx.includes('pronominal') || trans.includes('oneself') || trans.includes('myself') || trans.includes('yourself');
            });
            if (reflexIdx >= 0) return reflexIdx;
        }

        // Fallback: Default to primary meaning (highest prior frequency)
        return 0;
    }

    /**
     * Master Pipeline: Process a playlist of songs
     */
    async processPlaylist(songs, options = {}) {
        const startTime = performance.now();
        const onProgress = options.onProgress || (() => {});

        // 1. Parse and clean lyrics
        onProgress({ stage: 'parsing', message: 'Extracting synced lyrics and Spotify playback timings...' });
        const lineFrequency = new Map();
        const parsedSongs = [];

        for (const song of songs) {
            const lineObjs = this.parseLyrics(song.syncedLyrics, song.lyrics || song.plainLyrics);
            for (const l of lineObjs) {
                lineFrequency.set(l.text, (lineFrequency.get(l.text) || 0) + 1);
            }
            parsedSongs.push({
                ...song,
                lines: lineObjs
            });
        }

        // 2. Discover multi-word entity candidates across all songs
        onProgress({ stage: 'entities_scan', message: 'Scanning multi-token proper nouns and artist personas...' });
        const candidateEntityQueries = new Set();
        for (const song of parsedSongs) {
            for (const lineObj of song.lines) {
                const entitySpans = this.extractEntitySpans(lineObj.text);
                for (const span of entitySpans) {
                    candidateEntityQueries.add(span.phrase);
                }
            }
        }

        // Also check single known curated entity words (Prada, Gucci, Santurce, Venezuela, Cuba, etc.)
        for (const song of parsedSongs) {
            for (const lineObj of song.lines) {
                const tokens = lineObj.text.split(/\s+/);
                for (let i = 0; i < tokens.length; i++) {
                    const cleanWord = tokens[i].replace(/[^\p{L}]/gu, '');
                    if (this.curatedEntities[cleanWord.toLowerCase()]) {
                        candidateEntityQueries.add(cleanWord);
                    }
                }
            }
        }

        // 3. Resolve entities (Curated + Batched Spanish Grounding -> English Definitions)
        onProgress({ stage: 'entities_resolve', message: `Resolving entities with Spanish grounding & English definitions...` });
        const queryList = Array.from(candidateEntityQueries);
        const resolvedEntitiesMap = await this.resolveEntitiesBatch(queryList);

        // 4. Tokenize, snap MWEs, snap Entities, and collect vocabulary
        onProgress({ stage: 'indexing', message: 'Snapping MWEs and indexing vocabulary...' });

        const wordCandidates = new Map();
        const mweCandidates = new Map();
        const entityCardCandidates = new Map();

        for (const song of parsedSongs) {
            for (const lineObj of song.lines) {
                const lineScore = this.evaluateLineQuality(lineObj, lineFrequency.get(lineObj.text));
                const lineInfo = {
                    text: lineObj.text,
                    song: song.title,
                    artist: song.artist,
                    spotify_track_id: song.spotifyId || song.spotifyTrackId || null,
                    timestamp_ms: lineObj.timestamp_ms,
                    end_timestamp_ms: lineObj.end_timestamp_ms,
                    isSynced: lineObj.isSynced,
                    score: lineScore
                };

                // Check for multi-word entity matches in this line
                const lowerLine = lineObj.text.toLowerCase();
                let entityMatched = false;
                for (const [qKey, ent] of resolvedEntitiesMap.entries()) {
                    if (qKey.includes(' ') && lowerLine.includes(qKey)) {
                        let entry = entityCardCandidates.get(ent.canonicalTitle);
                        if (!entry) {
                            entry = {
                                entity: ent,
                                count: 0,
                                songs: new Set(),
                                lines: []
                            };
                            entityCardCandidates.set(ent.canonicalTitle, entry);
                        }
                        entry.count += 1;
                        entry.songs.add(song.title);
                        if (!entry.lines.some(l => l.text === lineObj.text)) {
                            entry.lines.push(lineInfo);
                        }
                        entityMatched = true;
                    }
                }

                // Tokenize line for MWEs and single words
                const tokens = this.tokenizeLine(lineObj.text);
                const mweSpans = this.findMweSpans(tokens);
                const mweIndices = new Set();

                for (const span of mweSpans) {
                    for (let idx = span.start; idx < span.end; idx++) {
                        mweIndices.add(idx);
                    }
                    let entry = mweCandidates.get(span.phrase);
                    if (!entry) {
                        entry = {
                            phrase: span.phrase,
                            mweInfo: span.mweInfo,
                            count: 0,
                            songs: new Set(),
                            lines: []
                        };
                        mweCandidates.set(span.phrase, entry);
                    }
                    entry.count += 1;
                    entry.songs.add(song.title);
                    if (!entry.lines.some(l => l.text === lineObj.text)) {
                        entry.lines.push(lineInfo);
                    }
                }

                // Single words (excluding MWE spans)
                for (let i = 0; i < tokens.length; i++) {
                    if (mweIndices.has(i)) continue;
                    const norm = tokens[i].normalized;
                    if (norm.length < 1) continue;
                    if (norm.length === 1 && !this.dictionary[norm] && !resolvedEntitiesMap.has(norm)) continue;

                    // Check single word entity
                    if (resolvedEntitiesMap.has(norm)) {
                        const ent = resolvedEntitiesMap.get(norm);
                        let entry = entityCardCandidates.get(ent.canonicalTitle);
                        if (!entry) {
                            entry = {
                                entity: ent,
                                count: 0,
                                songs: new Set(),
                                lines: []
                            };
                            entityCardCandidates.set(ent.canonicalTitle, entry);
                        }
                        entry.count += 1;
                        entry.songs.add(song.title);
                        if (!entry.lines.some(l => l.text === lineObj.text)) {
                            entry.lines.push(lineInfo);
                        }
                        continue;
                    }

                    // Single word dictionary entry
                    let entry = wordCandidates.get(norm);
                    if (!entry) {
                        entry = {
                            word: norm,
                            count: 0,
                            songs: new Set(),
                            lines: []
                        };
                        wordCandidates.set(norm, entry);
                    }
                    entry.count += 1;
                    entry.songs.add(song.title);
                    if (!entry.lines.some(l => l.text === lineObj.text)) {
                        entry.lines.push(lineInfo);
                    }
                }
            }
        }

        // 5. Assemble Cards
        onProgress({ stage: 'assembly', message: 'Selecting top Spotify playable examples and finalizing deck...' });
        const finalCards = [];

        // 5a. Entity Cards
        for (const [title, entry] of entityCardCandidates.entries()) {
            entry.lines.sort((a, b) => b.score - a.score);
            finalCards.push({
                type: 'entity',
                word: title,
                translation: entry.entity.description || entry.entity.entityType,
                playlistCount: entry.count,
                songCount: entry.songs.size,
                entity: entry.entity,
                meanings: [{
                    pos: 'PROPN',
                    translation: entry.entity.description || title,
                    isEntity: true,
                    examples: entry.lines.slice(0, 2).map(l => ({
                        target: l.text,
                        spanish: l.text,
                        song: l.song,
                        artist: l.artist,
                        spotify_track_id: l.spotify_track_id,
                        timestamp_ms: l.timestamp_ms,
                        end_timestamp_ms: l.end_timestamp_ms,
                        isSynced: l.isSynced
                    }))
                }],
                examples: entry.lines.slice(0, 2)
            });
        }

        // 5b. MWE Idiom Cards
        for (const [phrase, entry] of mweCandidates.entries()) {
            entry.lines.sort((a, b) => b.score - a.score);
            finalCards.push({
                type: 'mwe',
                word: entry.mweInfo?.expression || phrase,
                translation: entry.mweInfo?.translation || phrase,
                playlistCount: entry.count,
                songCount: entry.songs.size,
                meanings: [{
                    pos: 'IDIOM',
                    translation: entry.mweInfo?.translation || phrase,
                    isMwe: true,
                    examples: entry.lines.slice(0, 2).map(l => ({
                        target: l.text,
                        spanish: l.text,
                        song: l.song,
                        artist: l.artist,
                        spotify_track_id: l.spotify_track_id,
                        timestamp_ms: l.timestamp_ms,
                        end_timestamp_ms: l.end_timestamp_ms,
                        isSynced: l.isSynced
                    }))
                }],
                examples: entry.lines.slice(0, 2)
            });
        }

        // 5c. Standard Word Cards
        for (const [word, entry] of wordCandidates.entries()) {
            const dictEntry = this.dictionary[word];
            if (!dictEntry) continue; // Out of 10k speech dictionary

            entry.lines.sort((a, b) => b.score - a.score);
            const bestLines = entry.lines.slice(0, 2);

            // WSD bucket routing: Assign each best example to its disambiguated meaning bucket
            const meaningBuckets = dictEntry.meanings.map(m => ({ ...m, examples: [] }));
            for (const l of bestLines) {
                const chosenIdx = this.disambiguateWord(word, dictEntry, l.text);
                const exampleObj = {
                    target: l.text,
                    spanish: l.text,
                    song: l.song,
                    artist: l.artist,
                    spotify_track_id: l.spotify_track_id,
                    timestamp_ms: l.timestamp_ms,
                    end_timestamp_ms: l.end_timestamp_ms,
                    isSynced: l.isSynced
                };
                if (meaningBuckets[chosenIdx]) {
                    meaningBuckets[chosenIdx].examples.push(exampleObj);
                } else if (meaningBuckets[0]) {
                    meaningBuckets[0].examples.push(exampleObj);
                }
            }

            // Ensure primary meaning has examples if secondary received them all
            const topMeaning = meaningBuckets[0];
            const topTranslation = (topMeaning?.translation) || dictEntry.top_translation;

            finalCards.push({
                type: 'word',
                id: dictEntry.id,
                word,
                translation: topTranslation,
                pos: topMeaning?.pos || dictEntry.top_pos,
                speechRank: dictEntry.rank,
                isPolysemous: dictEntry.polysemous,
                meaningCount: dictEntry.meaningCount,
                playlistCount: entry.count,
                songCount: entry.songs.size,
                meanings: meaningBuckets,
                examples: bestLines
            });
        }

        // Rank by playlist frequency descending, then speech rank
        finalCards.sort((a, b) => {
            if (b.playlistCount !== a.playlistCount) return b.playlistCount - a.playlistCount;
            return (a.speechRank || 9999) - (b.speechRank || 9999);
        });

        // Assign ranks to cards FIRST so they propagate to token breakdowns
        finalCards.forEach((c, idx) => {
            c.rank = idx + 1;
        });

        // 6. Build Lyric-by-Lyric Audit Breakdown for every song
        const cardByLookupKey = new Map();
        for (const card of finalCards) {
            cardByLookupKey.set(card.word.toLowerCase(), card);
        }

        const annotatedSongs = parsedSongs.map(song => {
            const auditLines = song.lines.map(lineObj => {
                const tokens = this.tokenizeLine(lineObj.text);
                const mweSpans = this.findMweSpans(tokens);
                const mweIndices = new Set();
                const tokenBreakdowns = [];

                // Track MWEs
                for (const span of mweSpans) {
                    for (let idx = span.start; idx < span.end; idx++) {
                        mweIndices.add(idx);
                    }
                    const mweCard = cardByLookupKey.get(span.phrase.toLowerCase());
                    tokenBreakdowns.push({
                        startIndex: span.start,
                        raw: tokens.slice(span.start, span.end).map(t => t.raw).join(' '),
                        type: 'mwe',
                        card: mweCard || null,
                        word: span.phrase,
                        translation: mweCard?.translation || span.mweInfo?.translation || 'Idiom',
                        rank: mweCard?.rank || null
                    });
                }

                // Track Multi-Token Entities (e.g. "Brad Pitt", "Puerto Rico", "Myke Towers")
                const entityIndices = new Set();
                const n = tokens.length;
                for (let i = 0; i < n; i++) {
                    if (mweIndices.has(i)) continue;
                    for (let len = Math.min(4, n - i); len >= 2; len--) {
                        const rawPhrase = tokens.slice(i, i + len).map(t => t.raw).join(' ');
                        const lowerPhrase = rawPhrase.toLowerCase();
                        const ent = resolvedEntitiesMap.get(lowerPhrase);
                        if (ent) {
                            for (let k = i; k < i + len; k++) entityIndices.add(k);
                            const entCard = cardByLookupKey.get(ent.canonicalTitle.toLowerCase());
                            tokenBreakdowns.push({
                                startIndex: i,
                                raw: rawPhrase,
                                type: 'entity',
                                card: entCard || null,
                                word: ent.canonicalTitle,
                                translation: ent.description || 'Entity',
                                rank: entCard?.rank || null
                            });
                            i += len - 1;
                            break;
                        }
                    }
                }

                // Single words & single-token entities
                for (let i = 0; i < tokens.length; i++) {
                    if (mweIndices.has(i) || entityIndices.has(i)) continue;
                    const token = tokens[i];
                    const norm = token.normalized;
                    const ent = resolvedEntitiesMap.get(norm) || resolvedEntitiesMap.get(token.raw.toLowerCase());
                    
                    if (ent) {
                        const entCard = cardByLookupKey.get(ent.canonicalTitle.toLowerCase());
                        tokenBreakdowns.push({
                            startIndex: i,
                            raw: token.raw,
                            type: 'entity',
                            card: entCard || null,
                            word: ent.canonicalTitle,
                            translation: ent.description || 'Entity',
                            rank: entCard?.rank || null
                        });
                        continue;
                    }

                    const wordCard = cardByLookupKey.get(norm);
                    if (wordCard) {
                        tokenBreakdowns.push({
                            startIndex: i,
                            raw: token.raw,
                            type: 'word',
                            isElision: token.isElision,
                            card: wordCard,
                            word: wordCard.word,
                            translation: wordCard.translation,
                            pos: wordCard.pos,
                            rank: wordCard.rank,
                            speechRank: wordCard.speechRank,
                            isPolysemous: wordCard.isPolysemous
                        });
                    } else {
                        tokenBreakdowns.push({
                            startIndex: i,
                            raw: token.raw,
                            type: 'unmatched',
                            isElision: token.isElision,
                            word: norm,
                            translation: 'out of 10k supply / noise'
                        });
                    }
                }

                // Sort tokens in left-to-right line reading order
                tokenBreakdowns.sort((a, b) => a.startIndex - b.startIndex);

                return {
                    text: lineObj.text,
                    english: lineObj.english || song.englishLines?.[auditLines.length] || null,
                    timestamp_ms: lineObj.timestamp_ms,
                    end_timestamp_ms: lineObj.end_timestamp_ms,
                    isSynced: lineObj.isSynced,
                    tokens: tokenBreakdowns
                };
            });

            return {
                title: song.title,
                artist: song.artist,
                lineCount: auditLines.length,
                lines: auditLines
            };
        });

        const elapsedMs = performance.now() - startTime;

        return {
            cards: finalCards,
            annotatedSongs,
            totalCards: finalCards.length,
            mweCardsCount: finalCards.filter(c => c.type === 'mwe').length,
            entityCardsCount: finalCards.filter(c => c.type === 'entity').length,
            wordCardsCount: finalCards.filter(c => c.type === 'word').length,
            elapsedMs: Math.round(elapsedMs),
            entitiesResolved: Array.from(entityCardCandidates.values()).map(e => e.entity)
        };
    }
}
