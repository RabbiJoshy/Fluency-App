function normaliseWord(value) {
    return String(value || '').trim().toLocaleLowerCase('es');
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
