-- A deliberate migration review date is not an answer. Existing rows stay unchanged.
ALTER TABLE item_state ADD COLUMN migration_review_at TEXT;
