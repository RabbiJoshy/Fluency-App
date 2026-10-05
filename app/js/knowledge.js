// Granular sense / expression knowledge layered over whole-card progress.
// Whole-card answers are the baseline; only explicit row-level answers create
// ItemProgress records. The newest card-level or item-level event wins.
import './state.js?v=e7a99941';
import { sendOrQueue } from './sync-queue.js?v=e7a99941';

const KNOWLEDGE_SCHEMA_VERSION = 1;

let indexedItemProgressSource = null;
let indexedItemProgressSize = -1;
let itemProgressByParent = new Map();
let knowledgeOverviewCard = null;
// The card whose one-tap exception still owes its untouched siblings a
// "known" mark (see commitPendingKnowledgeSiblings).
let knowledgeSiblingsPendingCard = null;
// Which section tab the open overview shows (Meanings / Expressions / …).
let knowledgeOverviewTab = '';

function normalizeKnowledgeText(value) {
    return String(value || '')
        .normalize('NFKC')
        .trim()
        .toLowerCase()
        .replace(/\s+/g, ' ');
}

function hashKnowledgeSignature(value) {
    let hash = 0x811c9dc5;
    const text = String(value || '');
    for (let i = 0; i < text.length; i++) {
        hash ^= text.charCodeAt(i);
        hash = Math.imul(hash, 0x01000193);
    }
    return (hash >>> 0).toString(16).padStart(8, '0');
}

function makeKnowledgeItem(
    card,
    type,
    signature,
    label,
    meaningIndex,
    cycleIndex = 0,
    legacySignatures = []
) {
    const itemKey = `k${KNOWLEDGE_SCHEMA_VERSION}:${type}:${hashKnowledgeSignature(signature)}`;
    const legacyItemIds = legacySignatures
        .filter(Boolean)
        .map(legacySignature =>
            `${card.fullId}~k${KNOWLEDGE_SCHEMA_VERSION}:${type}:${hashKnowledgeSignature(legacySignature)}`)
        .filter(itemId => itemId !== `${card.fullId}~${itemKey}`);
    return {
        itemId: `${card.fullId}~${itemKey}`,
        legacyItemIds: Array.from(new Set(legacyItemIds)),
        itemKey,
        parentWordId: card.fullId,
        type,
        label: String(label || ''),
        meaningIndex,
        cycleIndex,
        schemaVersion: KNOWLEDGE_SCHEMA_VERSION
    };
}

function knowledgeItemsForMeaning(card, meaning, meaningIndex) {
    if (!meaning || meaning.exampleOnly) return [];
    if (meaning.allMWEs?.length) {
        return meaning.allMWEs.map((mwe, cycleIndex) => {
            const identity = normalizeKnowledgeText(mwe.id || mwe.family || mwe.expression);
            return {
                ...makeKnowledgeItem(
                    card,
                    'expression',
                    `expression|${identity}`,
                    mwe.expression || mwe.family || 'Expression',
                    meaningIndex,
                    cycleIndex
                ),
                detail: mwe.translation || '',
                pos: 'MWE'
            };
        });
    }
    if (meaning.allClitics?.length) {
        return meaning.allClitics.map((clitic, cycleIndex) => ({
            ...makeKnowledgeItem(
                card,
                'clitic',
                `clitic|${normalizeKnowledgeText(clitic.form)}`,
                clitic.form || 'Clitic form',
                meaningIndex,
                cycleIndex
            ),
            detail: clitic.translation || '',
            pos: 'CLITIC'
        }));
    }
    if (meaning.pos === 'SENSE_CYCLE' && meaning.allSenses?.length) {
        return meaning.allSenses.map((sense, cycleIndex) => {
            const pos = sense.pos || meaning.cycle_pos || 'X';
            const translation = sense.translation || meaning.meaning || '';
            const context = sense.context || '';
            const stableSenseId = sense.senseId || sense.sense_id || sense.id || '';
            const stableAliases = sense.senseIdAliases || sense.sense_id_aliases || [];
            const fallbackSignature = `sense|${normalizeKnowledgeText(pos)}|${normalizeKnowledgeText(translation)}|${normalizeKnowledgeText(context)}`;
            return {
                ...makeKnowledgeItem(
                    card,
                    'sense',
                    stableSenseId
                        ? `sense-id|${normalizeKnowledgeText(stableSenseId)}`
                        : fallbackSignature,
                    translation,
                    meaningIndex,
                    cycleIndex,
                    stableSenseId
                        ? [fallbackSignature, ...stableAliases.map(id => `sense-id|${normalizeKnowledgeText(id)}`)]
                        : []
                ),
                detail: context,
                pos,
                headword: sense.headword || meaning.headword || ''
            };
        });
    }

    const pos = meaning.pos || 'X';
    const translation = meaning.meaning || meaning.translation || '';
    const context = meaning.context || '';
    const stableSenseId = meaning.senseId || meaning.sense_id || meaning.id || '';
    const stableAliases = meaning.senseIdAliases || meaning.sense_id_aliases || [];
    const isRare = Boolean(meaning.isRareSense);
    const type = isRare ? 'rare_sense' : 'sense';
    const fallbackSignature = `${isRare ? 'rare-sense' : 'sense'}|${normalizeKnowledgeText(pos)}|${normalizeKnowledgeText(translation)}|${normalizeKnowledgeText(context)}`;
    const item = {
        ...makeKnowledgeItem(
            card,
            type,
            stableSenseId
                ? `${isRare ? 'rare-sense-id' : 'sense-id'}|${normalizeKnowledgeText(stableSenseId)}`
                : fallbackSignature,
            translation || pos,
            meaningIndex,
            0,
            stableSenseId
                ? [fallbackSignature, ...stableAliases.map(id => `${isRare ? 'rare-sense-id' : 'sense-id'}|${normalizeKnowledgeText(id)}`)]
                : []
        ),
        detail: context,
        pos,
        headword: meaning.headword || '',
        isRare
    };
    if (stableSenseId && !isRare) {
        item.legacyItemIds.push(`${card.fullId}~k${KNOWLEDGE_SCHEMA_VERSION}:rare_sense:${hashKnowledgeSignature(`rare-sense-id|${normalizeKnowledgeText(stableSenseId)}`)}`);
    }
    return [item];
}

/**
 * The pill on the card back — one (POS, headword) group — as a learnable item.
 *
 * This is the granularity worth recording. Measured on the 9,338-card deck,
 * "by POS" (11,690 units), "by lemma" (10,721) and "by the pair" (11,897) are
 * within 10% of each other: only 693 headwords span more than one POS and only
 * 204 POS span more than one headword. So the pair is not a third option, it is
 * both of the other two, and it is the one that gets `fue` right — ir and ser
 * are separate readings that lemma-alone would merge and POS-alone would too.
 *
 * It is also robust to the errors this WSD actually makes. Its mistakes are
 * near-misses inside one part of speech and one headword — tiempo's "day" for
 * "time", hacer's "to take" for "to do" — which are wrong at sense level and
 * right here. Knowing `tiempo` is the noun tiempo is the real target; knowing
 * which of its near-equivalent glosses applies is not.
 *
 * Keyed on lemma alone, not the pair, so it lines up with the lemma rows the
 * surface migration already wrote to Sheets. Where a headword spans two POS the
 * two pills share one record, the same way an item inherits from its card.
 */
function knowledgeItemForPill(card, pos, headword) {
    if (!card?.fullId || !pos) return null;
    const label = headword || card.targetWord || '';
    return makeKnowledgeItem(
        card,
        'lemma',
        `lemma|${normalizeKnowledgeText(label)}`,
        label,
        -1
    );
}

function getPillKnowledgeItems(card) {
    if (!card?.fullId || !Array.isArray(card.meanings)) return [];
    const unique = new Map();
    card.meanings.forEach(meaning => {
        if (!meaning || meaning.exampleOnly) return;
        const pos = meaning.pos === 'SENSE_CYCLE'
            ? (meaning.cycle_pos || 'X') : meaning.pos;
        if (!pos || pos === 'MWE' || pos === 'CLITIC') return;
        const item = knowledgeItemForPill(card, pos, meaning.headword);
        if (item && !unique.has(item.itemId)) unique.set(item.itemId, item);
    });
    return Array.from(unique.values());
}

function getCardKnowledgeItems(card) {
    if (!card?.fullId || !Array.isArray(card.meanings)) return [];
    const unique = new Map();
    card.meanings
        .flatMap((meaning, index) => knowledgeItemsForMeaning(card, meaning, index))
        .forEach(item => {
            // Identical sense content or the same durable pipeline sense ID can
            // legitimately appear in more than one rendered group. It remains
            // one learnable item rather than inflating the card summary.
            if (!unique.has(item.itemId)) unique.set(item.itemId, item);
        });
    return Array.from(unique.values());
}

// Unused dictionary senses have durable sense IDs but are outside the main
// card's learnable menu. They enter knowledge only after the learner asks to
// see them; a whole-card answer never marks them by implication.
function getRareSenseKnowledgeItems(card) {
    if (!card?.fullId || !Array.isArray(card.unusedMenuSenses)) return [];
    const unique = new Map();
    const focusedIds = new Set((card.meanings || [])
        .filter(meaning => meaning?.isRareSense)
        .map(meaning => meaning.senseId || meaning.sense_id)
        .filter(Boolean));
    for (const sense of card.unusedMenuSenses) {
        const translation = String(sense?.meaning || sense?.translation || '').trim();
        if (!translation) continue;
        const pos = sense.pos || 'X';
        const context = sense.context || '';
        const senseId = sense.senseId || sense.sense_id || '';
        if (senseId && focusedIds.has(senseId)) continue;
        const signature = senseId
            ? `rare-sense-id|${normalizeKnowledgeText(senseId)}`
            : `rare-sense|${normalizeKnowledgeText(pos)}|${normalizeKnowledgeText(translation)}|${normalizeKnowledgeText(context)}`;
        const item = {
            ...makeKnowledgeItem(card, 'rare_sense', signature, translation, -1),
            detail: context,
            pos,
            example: sense.canonicalExample?.text || sense.canonical_example?.text || '',
            sourceSense: sense,
            isRare: true
        };
        if (senseId) {
            item.legacyItemIds.push(`${card.fullId}~k${KNOWLEDGE_SCHEMA_VERSION}:sense:${hashKnowledgeSignature(`sense-id|${normalizeKnowledgeText(senseId)}`)}`);
        }
        if (!unique.has(item.itemId)) unique.set(item.itemId, item);
    }
    return [...unique.values()];
}

// Rarer senses are marked where they are read, on the Rarer uses sheet
// (flashcards.js), so this overview lists only the card's own items.
function getKnowledgeOverviewItems(card) {
    return getCardKnowledgeItems(card);
}

// The knowledge item behind one row of the Rarer uses sheet. The sheet's row
// and this item are built from the same unusedMenuSenses entry; matching on
// the sense id (or, without one, on gloss, POS and context) keeps the item —
// and so every saved Known/Review mark — the one the overview always used.
function findRareSenseKnowledgeItem(card, row) {
    if (!card || !row) return null;
    const rowId = row.senseId || row.sense_id || '';
    const text = value => normalizeKnowledgeText(value || '');
    return getRareSenseKnowledgeItems(card).find(item => {
        const sense = item.sourceSense || {};
        const senseId = sense.senseId || sense.sense_id || '';
        if (rowId || senseId) return rowId === senseId;
        return text(sense.meaning || sense.translation) === text(row.translation)
            && text(sense.pos || 'X') === text(row.pos || 'X')
            && text(sense.context) === text(row.context);
    }) || null;
}

function getActiveKnowledgeItems(card) {
    if (!card?.meanings?.length) return [];
    if (currentGroupSelection?.members?.length) {
        return currentGroupSelection.members.flatMap(index =>
            knowledgeItemsForMeaning(card, card.meanings[index], index));
    }
    const meaning = card.meanings[currentMeaningIndex];
    const items = knowledgeItemsForMeaning(card, meaning, currentMeaningIndex);
    if (items.length <= 1) return items;
    return [items[currentMWEIndex % items.length]];
}

function newestIso(first, second) {
    const firstTime = parseProgressTimestamp(first);
    const secondTime = parseProgressTimestamp(second);
    if (!firstTime && !secondTime) return null;
    return firstTime >= secondTime ? first : second;
}

function mergeKnowledgeProgress(parent, item) {
    if (!parent && !item) return null;
    const parentTime = Math.max(
        parseProgressTimestamp(parent?.lastSeen),
        parseProgressTimestamp(parent?.lastCorrect),
        parseProgressTimestamp(parent?.lastWrong)
    );
    const itemTime = Math.max(
        parseProgressTimestamp(item?.lastSeen),
        parseProgressTimestamp(item?.lastCorrect),
        parseProgressTimestamp(item?.lastWrong)
    );
    const itemLastWrong = parseProgressTimestamp(item?.lastWrong);
    const itemLastCorrect = parseProgressTimestamp(item?.lastCorrect);
    const itemUnresolvedWrong = itemLastWrong > 0 && itemLastWrong >= itemLastCorrect;

    // An item with answers of its own keeps its own schedule. A later
    // whole-card "yes" was not an answer about it: that card showed the item
    // greyed as known, or completed the card by promoting the parent. Only a
    // newer whole-card "no" still reaches it.
    const parentLastWrong = parseProgressTimestamp(parent?.lastWrong);
    const parentWrongIsNewest = parentLastWrong > itemTime
        && parentLastWrong >= parseProgressTimestamp(parent?.lastCorrect);
    if (itemTime > 0 && !parentWrongIsNewest) {
        return {
            correct: (Number(parent?.correct) || 0) + (Number(item?.correct) || 0),
            wrong: (Number(parent?.wrong) || 0) + (Number(item?.wrong) || 0),
            lastCorrect: item.lastCorrect || null,
            lastWrong: item.lastWrong || null,
            lastSeen: newestIso(parent?.lastSeen, item?.lastSeen),
            srsStage: getSrsStage(item)
        };
    }

    const newest = itemTime > parentTime ? item : parent;
    return {
        correct: (Number(parent?.correct) || 0) + (Number(item?.correct) || 0),
        wrong: (Number(parent?.wrong) || 0) + (Number(item?.wrong) || 0),
        // If the item has an unresolved explicit wrong, a general parent card "yes"
        // must not overwrite it: only an explicit item-level correct can resolve it.
        lastCorrect: itemUnresolvedWrong
            ? (item?.lastCorrect || null)
            : newestIso(parent?.lastCorrect, item?.lastCorrect),
        lastWrong: newestIso(parent?.lastWrong, item?.lastWrong),
        lastSeen: newestIso(parent?.lastSeen, item?.lastSeen),
        // The schedule belongs to the newest answer source. Combined lifetime
        // counts are retained for history but must not inflate its interval.
        srsStage: itemUnresolvedWrong
            ? (item ? getSrsStage(item) : 0)
            : (newest ? getSrsStage(newest) : undefined)
    };
}

function getSpecificItemProgress(item) {
    if (!item?.itemId) return null;
    const candidateIds = new Set([item.itemId, ...(item.legacyItemIds || [])]);
    const parentIds = window.getProgressRecordIdsForCard?.(item.parentWordId) || [];
    for (const parentId of parentIds) {
        for (const itemId of Array.from(candidateIds)) {
            const separator = itemId.indexOf('~');
            if (separator >= 0) candidateIds.add(parentId + itemId.slice(separator));
        }
    }
    const legacy = Array.from(candidateIds)
        .map(itemId => itemProgressData?.[itemId])
        .filter(Boolean);
    if (legacy.length === 0) return null;
    return legacy.reduce((latest, candidate) => {
        const latestTime = Math.max(
            parseProgressTimestamp(latest?.lastSeen),
            parseProgressTimestamp(latest?.lastCorrect),
            parseProgressTimestamp(latest?.lastWrong)
        );
        const candidateTime = Math.max(
            parseProgressTimestamp(candidate?.lastSeen),
            parseProgressTimestamp(candidate?.lastCorrect),
            parseProgressTimestamp(candidate?.lastWrong)
        );
        return candidateTime > latestTime ? candidate : latest;
    });
}

function getKnowledgeItemState(card, item) {
    const parentId = card?.fullId || item?.parentWordId;
    const parent = window.getMergedWordProgress?.(parentId, card?.targetWord)
        || progressData?.[parentId];
    const specific = getSpecificItemProgress(item);
    if (item?.isRare || item?.type === 'rare_sense') return getProgressState(specific);
    return getProgressState(mergeKnowledgeProgress(parent, specific));
}

function getCardKnowledgeSummary(card) {
    const items = getCardKnowledgeItems(card);
    const states = items.map(item => getKnowledgeItemState(card, item));
    return {
        total: items.length,
        learned: states.filter(state => state.learned).length,
        review: states.filter(state => state.needsReview).length,
        unseen: states.filter(state => !state.seen).length
    };
}

function getItemProgressForParent(parentWordId) {
    const source = itemProgressData || {};
    // O(1) staleness check — see the note on window.bumpProgressEpoch.
    const sourceSize = window.__progressEpoch || 0;
    if (indexedItemProgressSource !== source || indexedItemProgressSize !== sourceSize) {
        itemProgressByParent = new Map();
        for (const item of Object.values(source)) {
            if (!item?.parentWordId) continue;
            if (!itemProgressByParent.has(item.parentWordId)) {
                itemProgressByParent.set(item.parentWordId, []);
            }
            itemProgressByParent.get(item.parentWordId).push(item);
        }
        indexedItemProgressSource = source;
        indexedItemProgressSize = sourceSize;
    }
    return itemProgressByParent.get(parentWordId) || [];
}

function wordHasKnowledgeProgress(parentWordId, surface = '') {
    const parentIds = window.getProgressRecordIdsForCard?.(parentWordId, surface) || [parentWordId];
    return parentIds.some(id =>
        getItemProgressForParent(id).some(item => item.itemType !== 'rare_sense' && getProgressState(item).seen));
}

function getWordKnowledgeReviewInfo(parentWordId, surface = '') {
    const parent = window.getMergedWordProgress?.(parentWordId, surface)
        || progressData?.[parentWordId]
        || null;
    const parentState = getProgressState(parent);
    const parentIds = window.getProgressRecordIdsForCard?.(parentWordId, surface) || [parentWordId];
    const itemRows = parentIds.flatMap(id => getItemProgressForParent(id));
    const itemStates = itemRows.map(item => ({
        row: item,
        state: getProgressState(mergeKnowledgeProgress(parent, item))
    }));
    const allStates = [parentState, ...itemStates.map(item => item.state)];
    const hasIncorrect = allStates.some(state =>
        state.needsReview && state.reviewReason === 'incorrect');
    const hasDue = allStates.some(state => state.isDue);
    // A sparse item answer makes the card seen, but it does not silently make
    // the whole word known. Until every item is resolved (which promotes the
    // parent below), its never-marked siblings belong in Review, not Learn new.
    const isPartial = !parentState.seen
        && itemRows.some(item => item.itemType !== 'rare_sense' && getProgressState(item).seen);
    const needsReview = hasIncorrect || isPartial || hasDue;
    const relevantTimes = [];
    if (hasIncorrect) {
        allStates.forEach(state => {
            if (state.reviewReason === 'incorrect' && state.reviewAt) {
                relevantTimes.push(state.reviewAt);
            }
        });
    } else if (hasDue) {
        allStates.forEach(state => {
            if (state.isDue && state.nextReviewAt) relevantTimes.push(state.nextReviewAt);
        });
    } else if (isPartial) {
        itemRows.forEach(item => {
            const state = getProgressState(item);
            if (state.lastSeen) relevantTimes.push(state.lastSeen);
        });
    }
    let maxNeedfulnessScore = 0;
    let urgencyTier = null;
    if (needsReview) {
        const reviewStates = allStates.filter(s => s.needsReview);
        maxNeedfulnessScore = Math.max(0, ...reviewStates.map(s => s.needfulnessScore || 0));
        if (reviewStates.some(s => s.urgencyTier === 'never_right')) {
            urgencyTier = 'never_right';
        } else if (reviewStates.some(s => s.urgencyTier === 'critical')) {
            urgencyTier = 'critical';
        } else {
            urgencyTier = 'due';
        }
    }

    // Queue surfaces need one truthful, compact account of the latest answer.
    // Include item-level answers as well as the parent card: a rare meaning can
    // be the reason a word needs practice even when the parent was last right.
    const lastCorrect = Math.max(0, ...allStates.map(state => state.lastCorrect || 0));
    const lastWrong = Math.max(0, ...allStates.map(state => state.lastWrong || 0));

    return {
        needsReview,
        reason: hasIncorrect ? 'incorrect' : (hasDue ? 'due' : (isPartial ? 'partial' : null)),
        reviewAt: relevantTimes.length ? Math.min(...relevantTimes) : 0,
        urgencyTier,
        needfulnessScore: maxNeedfulnessScore,
        lastCorrect,
        lastWrong
    };
}

function wordNeedsKnowledgeReview(parentWordId, surface = '') {
    return getWordKnowledgeReviewInfo(parentWordId, surface).needsReview;
}

// One card shape for a word however it is reached, from a set or from Review.
// A part-known card keeps its known senses, flagged `isKnownSense` so they
// render greyed as Known and stay out of the cycle; the senses not yet known
// are the ones fronted and answered. "Known" is `learned`: a known sense that
// has fallen due is active again. A cycle row (expressions, clitics, possible
// meanings) drops its known entries, since it shows one entry at a time.
// Review also skips a word with nothing left to practise; a set shows it whole.
function buildKnowledgeAwareCard(card, { skipWhenNothingToPractise = false } = {}) {
    if (!card?.meanings?.length) return card;
    const focusedMeanings = [];
    let unresolvedCount = 0;
    let shaped = false;
    for (let meaningIndex = 0; meaningIndex < card.meanings.length; meaningIndex++) {
        const meaning = card.meanings[meaningIndex];
        const items = knowledgeItemsForMeaning(card, meaning, meaningIndex);
        const unresolved = items.filter(item => !getKnowledgeItemState(card, item).learned);
        unresolvedCount += unresolved.length;
        if (items.length && unresolved.length === 0) {
            focusedMeanings.push({ ...meaning, isKnownSense: true });
            shaped = true;
            continue;
        }
        if (unresolved.length === items.length) {
            focusedMeanings.push({ ...meaning });
            continue;
        }
        shaped = true;

        if (meaning.allMWEs?.length) {
            const keep = new Set(unresolved.map(item => item.cycleIndex));
            focusedMeanings.push({
                ...meaning,
                allMWEs: meaning.allMWEs.filter((_, index) => keep.has(index))
            });
        } else if (meaning.allClitics?.length) {
            const keep = new Set(unresolved.map(item => item.cycleIndex));
            focusedMeanings.push({
                ...meaning,
                allClitics: meaning.allClitics.filter((_, index) => keep.has(index))
            });
        } else if (meaning.pos === 'SENSE_CYCLE' && meaning.allSenses?.length) {
            const keep = new Set(unresolved.map(item => item.cycleIndex));
            const allSenses = meaning.allSenses.filter((_, index) => keep.has(index));
            focusedMeanings.push({
                ...meaning,
                allSenses,
                meaning: allSenses[0]?.translation || meaning.meaning
            });
        } else {
            focusedMeanings.push({ ...meaning });
        }
    }
    // Rare senses remain opt-in during ordinary study. Once explicitly marked
    // for review, they become active meanings on the same parent card.
    for (const item of getRareSenseKnowledgeItems(card)) {
        if (!getKnowledgeItemState(card, item).needsReview) continue;
        unresolvedCount += 1;
        shaped = true;
        const sense = item.sourceSense;
        focusedMeanings.push({
            ...sense,
            meaning: item.label,
            isRareSense: true,
            unassigned: false,
            percentage: 0,
            prominenceLabel: 'Rare',
            canonicalExample: sense.canonicalExample || sense.canonical_example || null,
            allExamples: sense.allExamples || []
        });
    }
    if (unresolvedCount === 0) {
        // Every sense is current on its own schedule. Review still shows the
        // word whole when the card itself is due, so the answer can resolve it
        // rather than leave a word counted in Review that never appears.
        const cardNeedsReview = window.getWordProgressState?.(card.fullId, card.targetWord)?.needsReview;
        return skipWhenNothingToPractise && !cardNeedsReview ? null : card;
    }
    if (!shaped) return card;
    const focusedRareIds = new Set(focusedMeanings
        .filter(meaning => meaning.isRareSense)
        .map(meaning => meaning.senseId || meaning.sense_id)
        .filter(Boolean));
    const firstActive = focusedMeanings.find(meaning => !meaning.isKnownSense) || focusedMeanings[0];
    return {
        ...card,
        meanings: focusedMeanings,
        unusedMenuSenses: (card.unusedMenuSenses || []).filter(sense =>
            !focusedRareIds.has(sense.senseId || sense.sense_id)),
        translation: firstActive?.meaning || card.translation,
        targetSentence: firstActive?.targetSentence || card.targetSentence,
        englishSentence: firstActive?.englishSentence || card.englishSentence,
        _grouping: null
    };
}

function cacheItemProgress() {
    window.cacheProgressLocally?.();
}

async function saveKnowledgeProgress(card, items, isCorrect) {
    if (!currentUser || currentUser.isGuest || !card?.fullId || !items?.length) return;
    const parentWasLearned = getWordProgressState(card.fullId, card.targetWord).learned;
    const timestamp = new Date().toISOString();
    for (const item of items) {
        const previous = getSpecificItemProgress(item);
        const existing = itemProgressData[item.itemId] || (previous ? {
            ...previous,
            itemId: item.itemId,
            parentWordId: card.fullId,
            itemType: item.type,
            label: item.label,
            schemaVersion: KNOWLEDGE_SCHEMA_VERSION
        } : {
            itemId: item.itemId,
            parentWordId: card.fullId,
            itemType: item.type,
            label: item.label,
            language: selectedLanguage,
            correct: 0,
            wrong: 0,
            lastCorrect: null,
            lastWrong: null,
            lastSeen: null,
            srsStage: 0,
            schemaVersion: KNOWLEDGE_SCHEMA_VERSION
        });
        existing.srsStage = advanceSrsStage(existing, isCorrect);
        if (isCorrect) {
            existing.correct = (Number(existing.correct) || 0) + 1;
            existing.lastCorrect = timestamp;
        } else {
            existing.wrong = (Number(existing.wrong) || 0) + 1;
            existing.lastWrong = timestamp;
        }
        existing.lastSeen = timestamp;
        existing.label = item.label;
        itemProgressData[item.itemId] = existing;
        window.bumpProgressEpoch?.();

        sendOrQueue({
            action: 'saveItem',
            sheet: 'Progress',
            mode: window.getProgressMode?.() || (activeArtist ? 'artist' : 'normal'),
            user: currentUser.initials,
            itemId: existing.itemId,
            parentWordId: existing.parentWordId,
            itemType: existing.itemType === 'expression' ? 'mwe' : existing.itemType,
            label: existing.label,
            language: existing.language,
            correct: existing.correct,
            wrong: existing.wrong,
            lastCorrect: existing.lastCorrect,
            lastWrong: existing.lastWrong,
            lastSeen: existing.lastSeen,
            srsStage: existing.srsStage,
            schemaVersion: existing.schemaVersion
        }, `saveItem|Progress|${existing.itemId}`);
    }
    cacheItemProgress();

    // Completing every sense/expression explicitly is equivalent to knowing
    // the card. Persist one parent correct so setup progress, coverage, and
    // future review filtering can recognise completion without downloading
    // the card schema merely to count its sparse ItemProgress rows.
    const summary = getCardKnowledgeSummary(card);
    if (!parentWasLearned && !items.every(item => item.type === 'rare_sense')
        && summary.total > 0 && summary.learned === summary.total) {
        await window.saveWordProgress?.(card, true);
    }
}

// Card entry stamps the visit so a whole-card answer can tell which senses
// the learner already answered one by one on this card.
function beginKnowledgeCardVisit(card) {
    if (!card) return;
    if (knowledgeSiblingsPendingCard && knowledgeSiblingsPendingCard !== card) {
        commitPendingKnowledgeSiblings(knowledgeSiblingsPendingCard);
    }
    card._knowledgeVisitStart = Date.now();
}

function answeredDuringVisit(card, item) {
    const visitStart = card?._knowledgeVisitStart || 0;
    const lastSeen = parseProgressTimestamp(getSpecificItemProgress(item)?.lastSeen);
    return visitStart > 0 && lastSeen >= visitStart;
}

// A whole-card answer on a part-known card is an answer about the senses it
// was testing: every sense not greyed as known, less those answered one by
// one on this visit. Greyed senses keep their own schedules. Returns false
// when the card has no known senses and the answer belongs to the card.
async function saveWholeCardKnowledgeAnswer(card, isCorrect) {
    // The whole-card answer supersedes a pending one-tap exception.
    if (knowledgeSiblingsPendingCard === card) knowledgeSiblingsPendingCard = null;
    if (!currentUser || currentUser.isGuest) return false;
    if (!card?.meanings?.some(meaning => meaning.isKnownSense)) return false;
    const items = card.meanings
        .flatMap((meaning, index) => meaning.isKnownSense ? [] : knowledgeItemsForMeaning(card, meaning, index))
        .filter(item => !answeredDuringVisit(card, item));
    if (items.length) await saveKnowledgeProgress(card, items, isCorrect);
    return true;
}

// The one-tap exception ("I only missed this one") marks the untouched
// siblings known when the learner leaves the card, not at the first tap, so
// a second missed sense is never briefly recorded as known.
async function commitPendingKnowledgeSiblings(card) {
    if (!card || knowledgeSiblingsPendingCard !== card) return;
    knowledgeSiblingsPendingCard = null;
    const siblings = getKnowledgeOverviewItems(card).filter(item =>
        !item.isRare && !getKnowledgeItemState(card, item).seen);
    if (siblings.length) await saveKnowledgeProgress(card, siblings, true);
}

function escapeKnowledgeHTML(value) {
    return String(value || '').replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]);
}

// Expressions arrive two ways: as MWE items, and (on current releases) as
// ordinary senses whose POS is PHRASE — `por qué`, `así que`. Both are
// expressions to the learner. The section is display only; item ids do not
// depend on it.
function knowledgeSectionLabel(item) {
    const type = item?.type;
    if (type === 'expression' || String(item?.pos || '').toUpperCase() === 'PHRASE') return 'Expressions';
    if (type === 'clitic') return 'Attached forms';
    return 'Meanings';
}

function renderKnowledgeOverviewButton(card) {
    if (!currentUser || currentUser.isGuest) return '';
    const items = getCardKnowledgeItems(card);
    // Show only meanings in the trigger count, matching the modal.
    const meaningItems = items.filter(item => knowledgeSectionLabel(item) === 'Meanings');
    const displayItems = meaningItems.length > 0 ? meaningItems : items;
    if (displayItems.length <= 1) return '';
    const learned = displayItems.filter(item => getKnowledgeItemState(card, item).learned).length;
    const total = displayItems.length;
    return `<button type="button" class="ref-tile knowledge-overview-trigger" aria-label="Meanings: ${learned}/${total} known" onclick="showKnowledgeOverview(event)">
        <svg class="ref-tile-icon" viewBox="10 10 26 26" aria-hidden="true">
            <path d="M12 13.5h18M12 21h18M12 28.5h11" class="knowledge-overview-icon-lines"/>
            <path d="m27 29 2.4 2.4L34 26.8" class="knowledge-overview-icon-check"/>
        </svg>
        <span class="ref-tile-label">${learned}/${total} known</span>
    </button>`;
}

function ensureKnowledgeOverviewModal() {
    let modal = document.getElementById('knowledgeOverviewModal');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'knowledgeOverviewModal';
    modal.className = 'knowledge-overview-modal';
    modal.hidden = true;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'knowledgeOverviewTitle');
    modal.innerHTML = `
        <div class="knowledge-overview-sheet">
            <header class="knowledge-overview-header">
                <h2 id="knowledgeOverviewTitle">Meanings</h2>
                <button type="button" class="knowledge-overview-close" aria-label="Close" onclick="closeKnowledgeOverview(event)">×</button>
            </header>
            <p class="knowledge-overview-hint">✓ the meanings you already know; × the ones you want to practise.</p>
            <div id="knowledgeOverviewSummary" class="knowledge-overview-summary"></div>
            <div id="knowledgeOverviewList" class="knowledge-overview-list"></div>
            <div class="knowledge-overview-footer" style="display: flex; justify-content: flex-end; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-color, rgba(255,255,255,0.1));">
                <button type="button" class="knowledge-overview-advance-btn" style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; background: var(--accent, #10b981); color: #fff; border: none; border-radius: 8px; font-weight: 600; font-size: 0.9rem; cursor: pointer;" onclick="saveAndNextCardFromKnowledge(event)">Save &amp; Next Card →</button>
            </div>
        </div>`;
    modal.addEventListener('click', event => {
        if (event.target === modal) closeKnowledgeOverview(event);
    });
    document.body.appendChild(modal);
    return modal;
}

function knowledgeOverviewRowsHTML(card, rows, { groupedByPos = false } = {}) {
    return rows.map(({ item, index }) => {
        const state = getKnowledgeItemState(card, item);
        const status = state.learned ? 'known' : (state.needsReview ? 'review' : 'unseen');
        const statusText = status === 'known' ? 'Known' : (status === 'review' ? 'Practice' : 'Unmarked');
        const pos = !groupedByPos && item.pos && (item.type === 'sense' || item.isRare)
            ? `<span class="knowledge-overview-pos">${escapeKnowledgeHTML(item.pos)}</span>` : '';
        // Rows read as they do on the card when the card has been drawn.
        const display = card._senseDisplay?.get(item.meaningIndex);
        const label = display?.label || item.label;
        const detail = display
            ? (display.label ? display.detail : item.detail)
            : [item.detail, item.isRare ? item.example : ''].filter(Boolean).join(' · ');
        const copy = `<span class="knowledge-overview-status" aria-label="${statusText}"></span>
            <span class="knowledge-overview-copy">${pos}<strong>${escapeKnowledgeHTML(label)}</strong>${detail ? `<small>${escapeKnowledgeHTML(detail)}</small>` : ''}</span>`;
        const lead = item.isRare
            ? `<div class="knowledge-overview-focus is-static">${copy}</div>`
            : `<button type="button" class="knowledge-overview-focus" onclick="focusKnowledgeOverviewItem(event, ${index})" title="Show this item on the card">${copy}</button>`;
        return `<div class="knowledge-overview-row is-${status}">
            ${lead}
            <div class="knowledge-overview-actions" aria-label="Knowledge for ${escapeKnowledgeHTML(item.label)}">
                <button type="button" class="knowledge-overview-mark mark-review${status === 'review' ? ' is-active' : ''}" onclick="markKnowledgeOverviewItem(event, ${index}, false)" aria-label="Mark for practice" title="Mark for practice">×</button>
                <button type="button" class="knowledge-overview-mark mark-known${status === 'known' ? ' is-active' : ''}" onclick="markKnowledgeOverviewItem(event, ${index}, true)" aria-label="Mark known" title="Mark known">✓</button>
            </div>
        </div>`;
    }).join('');
}

function renderKnowledgeOverview(card) {
    const modal = ensureKnowledgeOverviewModal();
    const items = getCardKnowledgeItems(card);
    const summaryEl = modal.querySelector('#knowledgeOverviewSummary');
    const listEl = modal.querySelector('#knowledgeOverviewList');

    // Title: the word itself
    const titleEl = modal.querySelector('#knowledgeOverviewTitle');
    if (titleEl) titleEl.textContent = card.targetWord || 'Meanings';

    // Build sections but only show Meanings (hide Expressions to simplify).
    // Expression knowledge is preserved in the data model; only the UI hides it.
    const sections = new Map();
    items.forEach((item, index) => {
        const label = knowledgeSectionLabel(item);
        if (!sections.has(label)) sections.set(label, []);
        sections.get(label).push({ item, index });
    });

    // Force to Meanings only — skip Expressions / Attached forms tabs
    const meaningRows = sections.get('Meanings') || [];
    let rows = meaningRows.length > 0 ? meaningRows : (sections.values().next().value || []);
    // Only the senses the card shows, in the card's order: a sense moved to
    // Rarer uses, or folded into another row, is not listed here.
    const display = card._senseDisplay;
    if (display?.size) {
        rows = rows
            .filter(({ item }) => display.has(item.meaningIndex) && !display.get(item.meaningIndex).hidden)
            .sort((a, b) => (display.get(a.item.meaningIndex).order - display.get(b.item.meaningIndex).order)
                || (a.item.cycleIndex - b.item.cycleIndex));
    }

    // The total repeats the one group's own count, so it shows only when the
    // card has several groups.
    const groupCount = new Set(rows.map(({ item }) => `${item.headword || ''}\0${item.pos || ''}`)).size;
    const displayedLearned = rows.filter(({ item }) => getKnowledgeItemState(card, item).learned).length;
    summaryEl.hidden = groupCount <= 1;
    summaryEl.innerHTML = groupCount <= 1 ? '' : `<strong>${displayedLearned}/${rows.length} known</strong>`;

    const groupable = rows.length > 0
        && rows.every(({ item }) => item.pos && item.pos !== 'MWE' && item.pos !== 'CLITIC');
    const sectionHTML = groupable
        ? knowledgeOverviewMeaningGroupsHTML(card, rows)
        : `<div class="knowledge-overview-rows">${knowledgeOverviewRowsHTML(card, rows)}</div>`;
    listEl.innerHTML = `<section class="knowledge-overview-section" role="region">${sectionHTML}</section>`;
}

// Meanings grouped as the card back groups them: one block per (lemma, POS)
// pair, headed by the same coloured POS label and lemma, so a learner marking
// `fue` can see which rows are ir and which are ser.
function knowledgeOverviewMeaningGroupsHTML(card, rows) {
    const groups = new Map();
    rows.forEach(row => {
        const pos = row.item.pos || 'X';
        const headword = String(row.item.headword || card.lemma || card.targetWord || '').trim();
        const key = `${headword}\0${pos}`;
        if (!groups.has(key)) groups.set(key, { pos, headword, rows: [] });
        groups.get(key).rows.push(row);
    });
    const posName = pos => (window.posDisplayName ? window.posDisplayName(pos) : pos);
    return Array.from(groups.values()).map(group => {
        const accent = window.getPosAccentRgb?.(group.pos) || '150, 160, 180';
        const known = group.rows.filter(({ item }) => getKnowledgeItemState(card, item).learned).length;
        return `<div class="knowledge-overview-group" style="--sense-match-rgb: ${accent};">
            <div class="knowledge-overview-group-head">
                <span class="knowledge-overview-group-pos">${escapeKnowledgeHTML(posName(group.pos))}</span>
                ${group.headword ? `<span class="knowledge-overview-group-lemma">${escapeKnowledgeHTML(group.headword)}</span>` : ''}
                <span class="knowledge-overview-group-count">${known}/${group.rows.length}</span>
            </div>
            ${knowledgeOverviewFamilyRunsHTML(card, group.rows)}
        </div>`;
    }).join('');
}

// A family row on the card ("if" over "whether" / "introduces a relevance
// conditional") keeps its heading here, with its sub-senses beneath it.
function knowledgeOverviewFamilyRunsHTML(card, rows) {
    const runs = [];
    for (const row of rows) {
        const family = card._senseDisplay?.get(row.item.meaningIndex)?.family || '';
        const last = runs[runs.length - 1];
        if (last && last.family === family) last.rows.push(row);
        else runs.push({ family, rows: [row] });
    }
    return runs.map(run => `${run.family
        ? `<div class="knowledge-overview-family">${escapeKnowledgeHTML(run.family)}</div>` : ''}<div class="knowledge-overview-rows${run.family ? ' is-family' : ''}">${knowledgeOverviewRowsHTML(card, run.rows, { groupedByPos: true })}</div>`).join('');
}

function selectKnowledgeOverviewTab(event, label) {
    event?.stopPropagation();
    knowledgeOverviewTab = label;
    if (knowledgeOverviewCard) renderKnowledgeOverview(knowledgeOverviewCard);
    document.querySelector('#knowledgeOverviewList .knowledge-overview-tab.is-active')?.focus();
}

function showKnowledgeOverview(event, options = {}) {
    event?.stopPropagation();
    const card = options.card || flashcards[currentIndex];
    if (!card) return;
    if (knowledgeOverviewCard !== card) knowledgeOverviewTab = '';
    knowledgeOverviewCard = card;
    const modal = ensureKnowledgeOverviewModal();
    renderKnowledgeOverview(card);
    modal.querySelector('.knowledge-overview-footer').hidden = card !== flashcards[currentIndex];
    modal.classList.remove('is-closing');
    modal.hidden = false;
    document.body.classList.add('knowledge-overview-open');
    window.sideDock?.placeById?.('knowledgeOverviewModal');
    modal.querySelector('.knowledge-overview-close')?.focus();
}

function closeKnowledgeOverview(event) {
    event?.stopPropagation();
    const modal = document.getElementById('knowledgeOverviewModal');
    document.body.classList.remove('knowledge-overview-open');
    if (!modal || modal.hidden) return;
    const sheet = modal.querySelector('.knowledge-overview-sheet');
    const finish = ({ requireClosing = false } = {}) => {
        // A reopen during the exit animation clears `is-closing`; the pending
        // animationend/timeout must not then hide the freshly opened sheet.
        if (requireClosing && !modal.classList.contains('is-closing')) return;
        modal.hidden = true;
        modal.classList.remove('is-closing');
    };
    // The sheet exits back through the top edge it entered from; hide it only
    // once that animation has played (or immediately for reduced motion).
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
    if (!sheet || reducedMotion) {
        finish();
        return;
    }
    modal.classList.add('is-closing');
    let settled = false;
    const settle = () => {
        if (settled) return;
        settled = true;
        sheet.removeEventListener('animationend', onAnimationEnd);
        finish({ requireClosing: true });
    };
    const onAnimationEnd = animationEvent => {
        if (animationEvent.target !== sheet) return;
        settle();
    };
    sheet.addEventListener('animationend', onAnimationEnd);
    setTimeout(settle, 400);
}

function focusKnowledgeOverviewItem(event, index) {
    event?.stopPropagation();
    const card = knowledgeOverviewCard;
    const item = card && getKnowledgeOverviewItems(card)[index];
    if (!card || !item || item.isRare) return;
    closeKnowledgeOverview();
    window.focusKnowledgeCardItem?.(item.meaningIndex, item.cycleIndex || 0);
}

async function markKnowledgeOverviewItem(event, index, isCorrect) {
    event?.stopPropagation();
    const card = knowledgeOverviewCard;
    const items = card && getKnowledgeOverviewItems(card);
    const item = items?.[index];
    if (!card || !item) return;

    // 1-tap exception flow: marking one sense unknown means the learner knew
    // the other unmarked ones. They are marked known on leaving the card
    // (commitPendingKnowledgeSiblings), so further misses can still be tapped.
    if (!isCorrect && !item.isRare) knowledgeSiblingsPendingCard = card;

    await saveKnowledgeProgress(card, [item], isCorrect);
    if (card === flashcards[currentIndex]) updateCard();
    renderKnowledgeOverview(card);
}

async function saveAndNextCardFromKnowledge(event) {
    event?.stopPropagation();
    const card = knowledgeOverviewCard;
    closeKnowledgeOverview(event);
    await commitPendingKnowledgeSiblings(card);
    if (typeof window.advanceToNextDeckCard === 'function') {
        window.advanceToNextDeckCard();
    } else if (typeof window.nextCard === 'function') {
        window.nextCard();
    }
}

// Kept as an empty compatibility hook for cached flashcards.js versions.
// Granular actions now live in the explicit overview instead of taking a
// permanent strip of vertical space from every card.
function renderKnowledgeControl() {
    return '';
}

async function markCurrentKnowledge(event, isCorrect) {
    event?.stopPropagation();
    const card = flashcards[currentIndex];
    const items = getActiveKnowledgeItems(card);
    if (!card || items.length === 0) return;
    await saveKnowledgeProgress(card, items, isCorrect);
    updateCard();
}

window.knowledgeItemsForMeaning = knowledgeItemsForMeaning;
window.getCardKnowledgeItems = getCardKnowledgeItems;
window.knowledgeItemForPill = knowledgeItemForPill;
window.getPillKnowledgeItems = getPillKnowledgeItems;
window.getActiveKnowledgeItems = getActiveKnowledgeItems;
window.getKnowledgeItemState = getKnowledgeItemState;
window.getCardKnowledgeSummary = getCardKnowledgeSummary;
window.wordHasKnowledgeProgress = wordHasKnowledgeProgress;
window.wordNeedsKnowledgeReview = wordNeedsKnowledgeReview;
window.getWordKnowledgeReviewInfo = getWordKnowledgeReviewInfo;
window.buildKnowledgeAwareCard = buildKnowledgeAwareCard;
window.saveKnowledgeProgress = saveKnowledgeProgress;
window.beginKnowledgeCardVisit = beginKnowledgeCardVisit;
window.saveWholeCardKnowledgeAnswer = saveWholeCardKnowledgeAnswer;
window.renderKnowledgeControl = renderKnowledgeControl;
window.renderKnowledgeOverviewButton = renderKnowledgeOverviewButton;
window.markCurrentKnowledge = markCurrentKnowledge;
window.showKnowledgeOverview = showKnowledgeOverview;
window.findRareSenseKnowledgeItem = findRareSenseKnowledgeItem;
window.closeKnowledgeOverview = closeKnowledgeOverview;
window.focusKnowledgeOverviewItem = focusKnowledgeOverviewItem;
window.markKnowledgeOverviewItem = markKnowledgeOverviewItem;
window.selectKnowledgeOverviewTab = selectKnowledgeOverviewTab;
window.saveAndNextCardFromKnowledge = saveAndNextCardFromKnowledge;
window.cacheItemProgress = cacheItemProgress;

document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const modal = document.getElementById('knowledgeOverviewModal');
    if (modal && !modal.hidden) closeKnowledgeOverview(event);
});
