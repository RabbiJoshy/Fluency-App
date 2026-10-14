// Shared by the app and Worker. Answer evidence and scheduling are separate.
export const REVIEW_INTERVAL_DAYS = [1, 3, 7, 14, 30, 60, 120, 240, 365];
export function reviewTimestamp(value) {
    const n = value ? Date.parse(value) : 0;
    return Number.isFinite(n) ? n : 0;
}
export function reviewCount(value) {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(0, Math.floor(n)) : 0;
}
export function reviewStage(progress) {
    const correct = reviewCount(progress?.correct);
    if (correct === 0) return 0;
    const raw = progress?.srsStage;
    const n = Number(raw);
    if (raw !== null && raw !== undefined && raw !== '' && Number.isFinite(n) && n >= 0) {
        return Math.min(Math.max(1, Math.floor(n)), REVIEW_INTERVAL_DAYS.length);
    }
    return Math.min(Math.max(1, correct - reviewCount(progress?.wrong)), REVIEW_INTERVAL_DAYS.length);
}
export function reviewIntervalDays(progress) {
    const stage = reviewStage(progress);
    if (!stage) return null;
    const c = reviewCount(progress?.correct), w = reviewCount(progress?.wrong);
    const factor = c + w ? Math.max(0.75, Math.min(1.25, 1.25 - w / (c + w) * 0.55)) : 1;
    return Math.max(1, Math.round(REVIEW_INTERVAL_DAYS[stage - 1] * factor));
}
export function reviewUnresolved(progress) {
    const c = reviewCount(progress?.correct), w = reviewCount(progress?.wrong);
    const lc = reviewTimestamp(progress?.lastCorrect), lw = reviewTimestamp(progress?.lastWrong);
    return w > 0 || lw > 0 ? (lw > 0 || lc > 0 ? lw > lc : c === 0) : false;
}
export function reviewNextAt(progress) {
    if (reviewUnresolved(progress) || !reviewCount(progress?.correct)) return 0;
    // Imported knowledge gets a review date, never a fabricated answer date.
    const imported = reviewTimestamp(progress?.migrationReviewAt);
    if (imported) return imported;
    const last = reviewTimestamp(progress?.lastCorrect), days = reviewIntervalDays(progress);
    return last && days ? last + days * 86400000 : 0;
}
