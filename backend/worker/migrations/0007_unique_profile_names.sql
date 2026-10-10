-- One identity per name, case-insensitively. name_key is already the
-- lower-cased, NFKC-normalised name, so a unique index on it is the
-- database-level guarantee behind createProfile()'s check (which also covers
-- two creates racing past that check).
--
-- This reverses the 0006 decision that names were intentionally non-unique.
-- Birthday no longer separates two people who share a name; the second one
-- must choose a different name.
--
-- Fails if two profiles already share a name_key. Check first:
--   SELECT name_key, COUNT(*) FROM learning_profiles GROUP BY 1 HAVING COUNT(*) > 1;
-- and remove or rename the extras (only empty profiles should be removed).
CREATE UNIQUE INDEX IF NOT EXISTS uq_learning_profile_name
ON learning_profiles(name_key);
