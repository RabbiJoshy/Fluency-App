-- A card with srs_stage = 0 is "never learned". Some rows carry stage 0 *and* a
-- correct answer with no later wrong answer: an older client saved the stage
-- before advancing it. The current client cannot produce that state (any
-- correct answer moves a card to stage >= 1), and the schedule treats stage 0
-- as "never due", so those cards sit frozen as learned forever.
--
-- Conservative repair: clear the stored stage to NULL ("no stage was ever
-- recorded"), which makes the app derive it from the counts exactly as it does
-- for any other unstaged card: max(1, correct - wrong). Those cards may then
-- come up for review. Nothing is invented.
--
-- DRY RUN FIRST (per user, how many rows this touches):
--   SELECT user_id, COUNT(*) FROM item_state
--   WHERE srs_stage = 0 AND correct_count > 0 AND unresolved = 0
--   GROUP BY user_id;
--
-- updated_at is bumped so delta-syncing clients (updated_at > their watermark)
-- pick the change up. due_at uses the worker ladder in store.js
-- (SRS_INTERVAL_DAYS = 1,3,7,14,30,60,120).
UPDATE item_state SET
  srs_stage = NULL,
  due_at = CASE WHEN last_correct_at = '' THEN NULL ELSE
    strftime('%Y-%m-%dT%H:%M:%fZ', last_correct_at,
      '+' || (CASE MIN(MAX(1, correct_count - incorrect_count), 7)
                WHEN 1 THEN 1 WHEN 2 THEN 3 WHEN 3 THEN 7 WHEN 4 THEN 14
                WHEN 5 THEN 30 WHEN 6 THEN 60 ELSE 120 END) || ' days') END,
  updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE srs_stage = 0 AND correct_count > 0 AND unresolved = 0;
