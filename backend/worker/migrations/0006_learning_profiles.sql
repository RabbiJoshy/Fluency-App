-- Progress keys are retained for legacy users; new profiles have independent IDs.
-- Names + birthdays are intentionally non-unique: collisions must be separable.
CREATE TABLE IF NOT EXISTS learning_profiles (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    name_key TEXT NOT NULL,
    birthday TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ('legacy', 'new')),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learning_profile_lookup
ON learning_profiles(name_key, birthday);
