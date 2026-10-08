// A recognisable progress directory, not secure authentication. No birth year.
export function profileFields(params) {
  const name = String(params.name || '').normalize('NFKC').trim().replace(/\s+/g, ' ');
  const birthday = String(params.birthday || '');
  if (!name || name.length > 40 || /[\u0000-\u001f\u007f]/u.test(name)) throw new Error('Enter a name or username (up to 40 characters).');
  const match = /^(\d{2})-(\d{2})$/.exec(birthday);
  const month = Number(match?.[1]), day = Number(match?.[2]);
  const days = [31,29,31,30,31,30,31,31,30,31,30,31];
  if (!match || month < 1 || month > 12 || day < 1 || day > days[month - 1]) throw new Error('Choose a valid birthday day and month.');
  return { name, nameKey: name.toLocaleLowerCase('en'), birthday };
}

async function contextFor(db, row) {
  const { results } = await db.prepare(`SELECT language, MAX(last_seen_at) AS last_studied,
    COUNT(*) AS studied_items FROM item_state WHERE user_id=?1 GROUP BY language
    ORDER BY last_studied DESC`).bind(row.user_id).all();
  return { id: row.user_id, name: row.display_name, birthday: row.birthday || '',
    legacy: row.origin === 'legacy', languages: results.map(item => item.language).filter(Boolean),
    lastStudied: results[0]?.last_studied || null,
    studiedItems: results.reduce((sum, item) => sum + item.studied_items, 0) };
}

export async function lookupProfiles(db, params) {
  const fields = profileFields(params);
  const { results } = await db.prepare(`SELECT * FROM learning_profiles
    WHERE name_key=?1 AND birthday=?2 ORDER BY created_at`).bind(fields.nameKey, fields.birthday).all();
  // Old profiles have no birthday. Offer their existing progress once, with
  // explicit recognition; registering it leaves every progress row untouched.
  const legacyId = fields.name.toUpperCase();
  if (/^[A-Z]{2,4}$/.test(legacyId)) {
    const claimed = await db.prepare('SELECT user_id FROM learning_profiles WHERE user_id=?1').bind(legacyId).first();
    const existing = await db.prepare(`SELECT user_id FROM users WHERE user_id=?1
      UNION SELECT user_id FROM item_state WHERE user_id=?1 LIMIT 1`).bind(legacyId).first();
    if (!claimed && existing) results.push({ user_id: legacyId, display_name: legacyId, origin:'legacy' });
  }
  return { profiles: await Promise.all(results.map(row => contextFor(db, row))) };
}

export async function createProfile(db, params) {
  const fields = profileFields(params);
  const id = String(params.id || '');
  if (!/^profile_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) throw new Error('Invalid profile ID.');
  await db.prepare(`INSERT INTO learning_profiles
    (user_id,display_name,name_key,birthday,origin,created_at) VALUES (?1,?2,?3,?4,'new',?5)
    ON CONFLICT(user_id) DO NOTHING`).bind(id,fields.name,fields.nameKey,fields.birthday,new Date().toISOString()).run();
  const row = await db.prepare('SELECT * FROM learning_profiles WHERE user_id=?1').bind(id).first();
  if (row.name_key !== fields.nameKey || row.birthday !== fields.birthday) throw new Error('Profile ID already in use.');
  return { profile: await contextFor(db,row) };
}

export async function claimLegacyProfile(db, params) {
  const fields = profileFields(params);
  const id = String(params.id || '');
  if (!/^[A-Z]{2,4}$/.test(id) || id !== fields.name.toUpperCase()) throw new Error('Legacy profile does not match.');
  const existing = await db.prepare(`SELECT user_id FROM users WHERE user_id=?1
    UNION SELECT user_id FROM item_state WHERE user_id=?1 LIMIT 1`).bind(id).first();
  if (!existing) throw new Error('Legacy profile no longer exists.');
  await db.prepare(`INSERT INTO learning_profiles
    (user_id,display_name,name_key,birthday,origin,created_at) VALUES (?1,?2,?3,?4,'legacy',?5)
    ON CONFLICT(user_id) DO NOTHING`).bind(id,fields.name,fields.nameKey,fields.birthday,new Date().toISOString()).run();
  const row = await db.prepare('SELECT * FROM learning_profiles WHERE user_id=?1').bind(id).first();
  if (row.name_key !== fields.nameKey || row.birthday !== fields.birthday) throw new Error('That old profile has already been linked to another birthday. Create a separate profile.');
  return { profile: await contextFor(db,row) };
}
