// The legacy `initials` property remains the internal progress key on the wire.
// A display name never becomes that key for a newly created profile.
export function userForProfile(profile) {
    return { initials: profile.id, profileId: profile.id, username: profile.name,
        birthday: profile.birthday, isGuest: false, legacyProfile: Boolean(profile.legacy) };
}

export function birthdayValue(day, month) {
    const d = Number(day), m = Number(month);
    const days = [31,29,31,30,31,30,31,31,30,31,30,31];
    if (!Number.isInteger(d) || !Number.isInteger(m) || m < 1 || m > 12 || d < 1 || d > days[m-1]) return '';
    return `${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}

export function optionalBirthdayValue(day, month) {
    if (!String(day).trim() && !String(month).trim()) return '';
    const birthday = birthdayValue(day, month);
    if (!birthday) throw new Error('Choose a valid birthday day and month, or leave both blank.');
    return birthday;
}

export function profileContext(profile) {
    const languages = (profile.languages || []).join(', ');
    const date = profile.lastStudied ? new Date(profile.lastStudied) : null;
    return [languages || 'No study sessions yet', date && !Number.isNaN(date.getTime())
        ? `Last studied ${date.toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'})}` : '',
        profile.legacy ? 'Existing profile — your progress will be kept' : ''].filter(Boolean).join(' · ');
}

export function showLoginError(message, field = null) {
    for (const id of ['profileNameError','loginFormError']) {
        const error = document.getElementById(id);
        const active = field === 'userInitials' ? id === 'profileNameError' : id === 'loginFormError';
        if (error) { error.textContent = active ? message : ''; error.hidden = !active || !message; }
    }
    for (const id of ['userInitials','birthdayDay','birthdayMonth']) {
        document.getElementById(id)?.setAttribute('aria-invalid', field === id ? 'true' : 'false');
    }
    if (field) document.getElementById(field)?.focus();
}

let epoch = 0, busy = false, pendingId = null;
export function resetProfileLogin() {
    epoch += 1;
    busy = false;
    pendingId = null;
    document.getElementById('profileMatches')?.replaceChildren();
    document.getElementById('profileMatchCards')?.replaceChildren();
    document.getElementById('profileMatchModal')?.classList.add('hidden');
    showLoginError('');
    setBusy(false);
}

function setBusy(value) {
    busy = value;
    const submit = document.getElementById('submitInitialsBtn');
    if (submit) { submit.disabled = value; submit.textContent = value ? 'Checking…' : 'Continue'; }
    for (const id of ['userInitials','birthdayDay','birthdayMonth']) {
        const field = document.getElementById(id);
        if (field) field.disabled = value;
    }
    document.getElementById('profileMatches')?.querySelectorAll('button').forEach(button => { button.disabled = value; });
    document.getElementById('profileMatchCards')?.querySelectorAll('button').forEach(button => { button.disabled = value; });
    const createBtn = document.getElementById('profileMatchCreateBtn');
    if (createBtn) createBtn.disabled = value;
}

async function requestProfiles(action, fields) {
    let url = window.GOOGLE_SCRIPT_URL || window.config?.publicServices?.progressSyncUrl;
    if (!url) {
        const response = await fetch('config/config.json', {cache:'no-store'});
        if (!response.ok) throw new Error('Profile lookup is unavailable. Please try again.');
        url = (await response.json()).publicServices?.progressSyncUrl;
    }
    if (!url) throw new Error('Profile lookup is unavailable. Please try again.');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
        const response = await fetch(url, {method:'POST',body:JSON.stringify({action,...fields}),signal:controller.signal});
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || 'Profile lookup failed. Please try again.');
        return result.data;
    } catch (error) {
        if (error.name === 'AbortError' || error instanceof TypeError) throw new Error('Could not reach your profiles. Check your connection and try again.');
        throw error;
    } finally { clearTimeout(timer); }
}

export async function submitProfileLogin(onSelected) {
    // Also wire these when this module is the boot-error fallback.
    const form = document.getElementById('loginForm');
    if (form && !form.dataset.profilesWired) {
        form.dataset.profilesWired = '1';
        ['userInitials','birthdayInput','birthdayDay','birthdayMonth'].forEach(id => {
            document.getElementById(id)?.addEventListener('input', resetProfileLogin);
        });
        // A different username may not have a birthday password at all.
        document.getElementById('userInitials')?.addEventListener('input', () => form.classList.remove('needs-birthday'));
        document.getElementById('cancelLoginBtn')?.addEventListener('click', resetProfileLogin);
    }
    if (busy) return;
    const name = document.getElementById('userInitials').value.normalize('NFKC').trim().replace(/\s+/g,' ');
    let birthday;
    showLoginError('');
    if (!name || name.length > 40 || /[\u0000-\u001f\u007f]/u.test(name)) {
        showLoginError('Enter a username (up to 40 characters).', 'userInitials'); return;
    }
    const bdayDay = document.getElementById('birthdayDay');
    const bdayMonth = document.getElementById('birthdayMonth');
    try {
        birthday = optionalBirthdayValue(bdayDay?.value, bdayMonth?.value);
    } catch (error) { showLoginError(error.message, 'birthdayDay'); return; }
    const fields = {name,birthday};
    const attempt = ++epoch;
    document.getElementById('profileMatches')?.replaceChildren();
    document.getElementById('profileMatchCards')?.replaceChildren();
    setBusy(true);
    const choose = async profile => {
        if (attempt !== epoch || busy) return;
        setBusy(true);
        try {
            if (profile.needsLink) {
                profile = (await requestProfiles('claimLegacyProfile',{...fields,id:profile.id})).profile;
            }
            if (attempt !== epoch) return;
            const user = userForProfile(profile);
            localStorage.setItem('flashcardUser',JSON.stringify(user));
            await onSelected(user);
        } catch (error) { if (attempt === epoch) showLoginError(error.message); }
        finally { if (attempt === epoch) setBusy(false); }
    };
    const create = async () => {
        if (attempt !== epoch || busy) return;
        setBusy(true);
        // Retry the same ID after a timeout: a delayed response cannot create
        // duplicate profiles or strand the first profile's progress.
        pendingId ||= `profile_${crypto.randomUUID()}`;
        try {
            const {profile} = await requestProfiles('createProfile',{...fields,id:pendingId});
            if (attempt !== epoch) return;
            setBusy(false);
            await choose(profile);
        } catch (error) { if (attempt === epoch) showLoginError(error.message); }
        finally { if (attempt === epoch) setBusy(false); }
    };
    try {
        const {profiles} = await requestProfiles('lookupProfiles',fields);
        if (attempt !== epoch) return;
        setBusy(false);
        const loggingIn = form?.dataset.mode === 'login';
        if (loggingIn) {
            // Logging in asks only for the username. The birthday is a password,
            // so it is requested only when a matching profile has one set.
            if (!profiles.length) {
                const hadBirthday = Boolean(birthday);
                showLoginError(hadBirthday
                    ? 'That birthday does not match this username.'
                    : 'No account found with that username. Use Create account instead.',
                    hadBirthday ? 'birthdayDay' : 'userInitials');
                return;
            }
            const protectedProfile = profiles.some(p => p.birthday);
            const unlocked = profiles.some(p => !p.birthday || p.birthday === birthday);
            if (protectedProfile && !birthday && !profiles.some(p => !p.birthday)) {
                form.classList.add('needs-birthday');
                showLoginError('Enter your birthday to continue.', 'birthdayDay');
                return;
            }
            if (!unlocked) {
                form.classList.add('needs-birthday');
                showLoginError('That birthday does not match this username.', 'birthdayDay');
                return;
            }
        }
        if (!profiles.length) { await create(); return; }
        const modal = document.getElementById('profileMatchModal');
        const cardsHost = document.getElementById('profileMatchCards') || document.getElementById('profileMatches');
        if (cardsHost) cardsHost.replaceChildren();
        for (const profile of profiles) {
            const card = document.createElement('div'); card.className = 'profile-match-card';
            const info = document.createElement('div'); info.className = 'profile-match-info';
            const nameLabel = document.createElement('strong'); nameLabel.className = 'profile-match-name'; nameLabel.textContent = profile.name;
            const context = document.createElement('p'); context.className = 'profile-match-context'; context.textContent = profileContext(profile);
            info.append(nameLabel, context);
            const button = document.createElement('button'); button.type = 'button'; button.className = 'product-primary-action profile-match-choose-btn';
            button.textContent = 'Yes, continue';
            button.addEventListener('click', async () => {
                modal?.classList.add('hidden');
                await choose(profile);
            });
            card.append(info, button);
            cardsHost.appendChild(card);
        }
        const separateBtn = document.getElementById('profileMatchCreateBtn');
        if (separateBtn) {
            separateBtn.onclick = async () => {
                modal?.classList.add('hidden');
                await create();
            };
        }
        const closeBtn = document.getElementById('closeProfileMatchModal');
        if (closeBtn) {
            closeBtn.onclick = () => {
                modal?.classList.add('hidden');
                setBusy(false);
            };
        }
        if (modal) {
            modal.classList.remove('hidden');
            modal.querySelector('button')?.focus();
        } else {
            cardsHost?.querySelector('button')?.focus();
        }
    } catch (error) { if (attempt === epoch) showLoginError(error.message); }
    finally { if (attempt === epoch) setBusy(false); }
}
