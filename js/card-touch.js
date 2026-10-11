// Touch arbitration only: existing click handlers continue to own taps.
const GRADE_DISTANCE = 50;
const LOCK_DISTANCE = 10;
const AXIS_LEAD = 1.15;
const CONTROL = 'button, a, input, select, textarea, [role="button"], [onclick]';

export function installCardTouch({ card, correctIndicator, incorrectIndicator,
    grade, cycle, feedback, busy, cancelPress = () => {},
    getStyle = element => getComputedStyle(element) }) {
    if (card.dataset.touchGesturesInstalled) return;
    card.dataset.touchGesturesInstalled = '1';
    let drag = null;
    let cancelled = false;
    let suppressClickUntil = 0;

    function clearVisuals() {
        card.classList.remove('swiping');
        card.style.transform = '';
        correctIndicator.classList.remove('visible');
        incorrectIndicator.classList.remove('visible');
        feedback(null);
    }
    function cancel() {
        if (drag) {
            suppressClickUntil = Date.now() + 700;
            cancelled = true;
        }
        cancelPress();
        drag = null;
        clearVisuals();
    }
    function scrollPort(target) {
        for (let node = target; node && node !== card; node = node.parentElement) {
            if (/(auto|scroll)/.test(getStyle(node).overflowY)
                && node.scrollHeight > node.clientHeight) return node;
        }
        return null;
    }
    function updatePosition(touch) {
        drag.x = touch.clientX - drag.startX;
        drag.y = touch.clientY - drag.startY;
        drag.maxMovement = Math.max(drag.maxMovement, Math.hypot(drag.x, drag.y));
        const x = Math.abs(drag.x), y = Math.abs(drag.y);
        if (!drag.axis && Math.max(x, y) >= LOCK_DISTANCE) {
            if (x > y * AXIS_LEAD) drag.axis = 'horizontal';
            else if (y > x * AXIS_LEAD) drag.axis = 'vertical';
        }
    }
    function gradeDirection() {
        if (drag.axis !== 'horizontal' || Math.abs(drag.x) < GRADE_DISTANCE
            || Math.abs(drag.x) <= Math.abs(drag.y) * AXIS_LEAD) return null;
        return drag.x > 0 ? 'correct' : 'incorrect';
    }
    card.addEventListener('touchstart', event => {
        if (event.touches.length !== 1 || busy()) { cancel(); return; }
        // The set scrubber has its own drag navigation. It keeps ownership.
        if (event.target.closest('.card-back-scrubber')) { cancel(); return; }
        suppressClickUntil = 0;
        cancelled = false;
        const touch = event.touches[0];
        drag = {
            id: touch.identifier, startX: touch.clientX, startY: touch.clientY,
            x: 0, y: 0, axis: null, maxMovement: 0,
            control: Boolean(event.target.closest(CONTROL)),
            scroll: scrollPort(event.target),
            flipped: card.classList.contains('flipped')
        };
    }, { passive: true });

    card.addEventListener('touchmove', event => {
        if (!drag) return;
        if (event.touches.length !== 1 || busy()) { cancel(); return; }
        const touch = event.touches[0];
        if (touch.identifier !== drag.id) { cancel(); return; }
        updatePosition(touch);
        if (drag.maxMovement >= LOCK_DISTANCE) cancelPress();
        // Native vertical scrolling owns scrollports. Outside them, keep
        // the existing vertical content cycling rather than scrolling the page.
        if (drag.axis === 'horizontal' || !drag.scroll) {
            if (event.cancelable) event.preventDefault();
        }
        if (drag.axis !== 'horizontal') return;
        card.classList.add('swiping');
        card.style.transform = `translateX(${drag.x}px) rotate(${drag.x / 20}deg)`
            + (drag.flipped ? ' rotateY(180deg)' : '');
        const direction = gradeDirection();
        correctIndicator.classList.toggle('visible', direction === 'correct');
        incorrectIndicator.classList.toggle('visible', direction === 'incorrect');
        feedback(direction);
    }, { passive: false });

    // Capture ends before button ontouchend handlers: a grading drag must
    // not also play audio, navigate, or open a menu on release.
    card.addEventListener('touchend', event => {
        if (!drag) {
            // Fingers lifted after a multiple-touch cancellation must not
            // reach a button's inline touchend activation either.
            if (cancelled) {
                if (event.cancelable) event.preventDefault();
                event.stopImmediatePropagation();
                if (!event.touches.length) cancelled = false;
            }
            return;
        }
        if (event.touches.length || busy()) { cancel(); return; }
        const touch = Array.from(event.changedTouches).find(item => item.identifier === drag.id);
        if (!touch) { cancel(); return; }
        updatePosition(touch);
        const direction = gradeDirection();
        const finished = drag;
        drag = null;
        clearVisuals();
        if (direction || finished.maxMovement >= LOCK_DISTANCE) {
            cancelPress();
            suppressClickUntil = Date.now() + 700;
            if (event.cancelable) event.preventDefault();
            event.stopImmediatePropagation();
        }
        if (direction) grade(direction);
        else if (finished.axis === 'vertical' && !finished.scroll && !finished.control
            && finished.flipped && Math.abs(finished.y) > 12) {
            cycle(finished.y < 0 ? 1 : -1);
        }
        // A stationary tap is handled once by the existing click path.
    }, { passive: false, capture: true });

    card.addEventListener('touchcancel', cancel, { passive: true });
    card.addEventListener('click', event => {
        // Keyboard activation (detail 0) and a known mouse click remain valid.
        if (event.detail === 0 || event.sourceCapabilities?.firesTouchEvents === false) return;
        if (Date.now() < suppressClickUntil) {
            event.preventDefault();
            event.stopImmediatePropagation();
        }
    }, true);
}
