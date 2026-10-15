const STORAGE_KEY = 'fluency_preferred_ai_v1';
const PROVIDERS = {
    chatgpt: { name: 'ChatGPT', url: 'https://chatgpt.com/' },
    claude: { name: 'Claude', url: 'https://claude.ai/' }
};

const CHATGPT_SVG = `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><title>ChatGPT</title><path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1683a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4947zm-9.66-4.1354a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1402-1.6564zm-1.6704-9.3364a4.4755 4.4755 0 0 1 2.3418-1.9729v5.6725a.7901.7901 0 0 0 .388.6813l5.8428 3.3685-2.02 1.1683a.071.071 0 0 1-.071 0l-4.8303-2.7913a4.4944 4.4944 0 0 1-1.6513-6.1264zM16.598 12.012l-5.8428-3.3685 2.02-1.1683a.071.071 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1 1.6513 6.1264 4.4755 4.4755 0 0 1-2.3418 1.9729v-5.6725a.7901.7901 0 0 0-.388-.6813zm4.6568-1.6366l-.142-.0852-4.783-2.7582a.7712.7712 0 0 0-.7806 0l-5.8428 3.3685v-2.3324a.0804.0804 0 0 1 .0332-.0615L14.26 4.0498a4.4992 4.4992 0 0 1 6.1402 1.6564 4.4708 4.4708 0 0 1 .5346 3.0137zm-9.518-2.6186a.7948.7948 0 0 0-.3927.6813v6.7369l-2.02-1.1683a.071.071 0 0 1-.038-.052V9.0498a4.504 4.504 0 0 1 4.4945-4.4947 4.4755 4.4755 0 0 1 2.8764 1.0408l-.1419.0804zm-1.2588 5.795l2.7677-1.5979 2.7677 1.5979v3.1957l-2.7677 1.5979-2.7677-1.5979z"/></svg>`;

const CLAUDE_SVG = `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><title>Claude</title><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>`;

const PROVIDER_SVGS = {
    chatgpt: CHATGPT_SVG,
    claude: CLAUDE_SVG
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
    const avatar = document.getElementById('preferredAiAvatar');
    const trigger = document.getElementById('preferredAiTrigger');
    const triggerIcon = document.getElementById('preferredAiTriggerIcon');
    const triggerLabel = document.getElementById('preferredAiTriggerLabel');
    const menu = document.getElementById('preferredAiMenu');
    const dropdown = document.getElementById('preferredAiDropdown');
    const login = document.getElementById('preferredAiLogin');

    if (!select && !trigger) return;

    const paint = () => {
        const current = preferredAi();
        if (select) select.value = current;

        const provider = PROVIDERS[current];
        if (login && provider) {
            login.href = provider.url;
            login.textContent = `Open ${provider.name} to sign in ↗`;
        }

        if (avatar) {
            avatar.className = `account-avatar account-avatar--ai is-${current}`;
            avatar.innerHTML = PROVIDER_SVGS[current] || '';
        }

        if (trigger) {
            if (triggerIcon) triggerIcon.innerHTML = PROVIDER_SVGS[current] || '';
            if (triggerLabel) triggerLabel.textContent = provider?.name || current;
        }

        if (menu) {
            menu.querySelectorAll('.preferred-ai-option').forEach(opt => {
                const isSelected = opt.getAttribute('data-value') === current;
                opt.setAttribute('aria-selected', isSelected ? 'true' : 'false');
                opt.classList.toggle('is-selected', isSelected);
            });
        }
    };

    const closeMenu = () => {
        if (!menu) return;
        menu.hidden = true;
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
        if (dropdown) dropdown.classList.remove('is-open');
    };

    const openMenu = () => {
        if (!menu) return;
        menu.hidden = false;
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
        if (dropdown) dropdown.classList.add('is-open');
    };

    if (trigger && menu) {
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            if (menu.hidden) {
                openMenu();
            } else {
                closeMenu();
            }
        });

        menu.addEventListener('click', (e) => {
            const option = e.target.closest('.preferred-ai-option');
            if (!option) return;
            const val = option.getAttribute('data-value');
            if (Object.hasOwn(PROVIDERS, val)) {
                savedPreference = val;
                try { localStorage.setItem(STORAGE_KEY, savedPreference); } catch (_) {}
                if (select) {
                    select.value = val;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
                paint();
                closeMenu();
                trigger.focus();
            }
        });

        document.addEventListener('click', (e) => {
            if (dropdown && !dropdown.contains(e.target)) {
                closeMenu();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && menu && !menu.hidden) {
                closeMenu();
                trigger.focus();
            }
        });
    }

    if (select) {
        select.addEventListener('change', () => {
            if (!Object.hasOwn(PROVIDERS, select.value)) return;
            savedPreference = select.value;
            try { localStorage.setItem(STORAGE_KEY, savedPreference); } catch (_) {}
            paint();
        });
    }

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
