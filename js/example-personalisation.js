function normaliseWord(value) {
    return String(value || '').trim().toLocaleLowerCase('es');
}

// A conservative pair check, not a semantic translation model. Normal length
// variation ties; only gross truncation/expansion or changed digits demotes a
// pair. This ranks the examples already selected by the release, never gates.
export function translationMismatchPenalty(example) {
    const target = String(example?.target || example?.spanish || '').trim();
    const english = String(example?.english || '').trim();
    if (!target || !english) return 0;
    const tokens = text => text.match(/[\p{L}\p{N}]+(?:['’][\p{L}\p{N}]+)*/gu) || [];
    const targetLength = tokens(target).length;
    const englishLength = tokens(english).length;
    const ratio = englishLength / Math.max(1, targetLength);
    const lengthMismatch = Math.max(targetLength, englishLength) >= 6
        && (ratio < 0.5 || ratio >= 2.2);
    const numbers = text => [...new Set(text.match(/\p{N}+/gu) || [])].sort();
    const targetNumbers = numbers(target), englishNumbers = numbers(english);
    // One side may spell a number out or format thousands differently. Only
    // compare equally sized, nonempty digit sets; absence is not a mismatch.
    const numberMismatch = targetNumbers.length > 0
        && targetNumbers.length === englishNumbers.length
        && targetNumbers.join('|') !== englishNumbers.join('|');
    return Number(lengthMismatch) + Number(numberMismatch);
}

// Words the learner is due to review, as one Set: examples containing one are
// ranked up, and a personalised line is shown only for one. The review queue
// already weighs misses, so this follows it rather than a separate
// "wrong in the last week" list.
export function collectReviewWords(dueReviewWords) {
    const words = new Set();
    for (const entry of dueReviewWords || []) {
        const word = normaliseWord(entry?.word);
        if (word) words.add(word);
    }
    return words;
}

export function filterPersonalisedExamples(examples, recentWrongWords) {
    const wrongWords = recentWrongWords instanceof Set
        ? recentWrongWords
        : new Set(Array.from(recentWrongWords || [], normaliseWord));
    return (examples || []).filter(example => {
        if (!example?.personalised) return true;
        return wrongWords.has(normaliseWord(example.reinforcement_word));
    });
}

export function exampleReinforcesRecentMistake(example, recentWrongWords) {
    return Boolean(
        example?.personalised
        && recentWrongWords?.has(normaliseWord(example.reinforcement_word))
    );
}
