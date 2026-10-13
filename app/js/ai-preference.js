const STORAGE_KEY = 'fluency_preferred_ai_v1';
const PROVIDERS = {
    chatgpt: { name: 'ChatGPT', url: 'https://chatgpt.com/' },
    claude: { name: 'Claude', url: 'https://claude.ai/' }
};
let savedPreference = null;

export function preferredAi() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (Object.hasOwn(PROVIDERS, saved)) return saved;
    } catch (_) { /* Keep the preference in this tab when storage is unavailable. */ }
    return savedPreference || 'chatgpt';
}

function initAiPreference() {
    const select = document.getElementById('preferredAiSelect');
    const login = document.getElementById('preferredAiLogin');
    if (!select || !login) return;
    const paint = () => {
        select.value = preferredAi();
        const provider = PROVIDERS[select.value];
        login.href = provider.url;
        login.textContent = `Open ${provider.name} to sign in ↗`;
    };
    select.addEventListener('change', () => {
        if (!Object.hasOwn(PROVIDERS, select.value)) return;
        savedPreference = select.value;
        try { localStorage.setItem(STORAGE_KEY, savedPreference); } catch (_) {}
        paint();
    });
    window.addEventListener('storage', event => {
        if (event.key === STORAGE_KEY) paint();
    });
    paint();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAiPreference, { once: true });
} else {
    initAiPreference();
}
