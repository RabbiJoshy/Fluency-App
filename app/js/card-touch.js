// Touch arbitration only: existing click handlers continue to own taps.
const GRADE_DISTANCE = 50;
const FLICK_DISTANCE = 22;
const FLICK_VELOCITY = 0.45;
const LOCK_DISTANCE = 10;
const AXIS_LEAD = 1.15;
const DAMPED_Y = 0.16;
const CONTROL = 'button, a, input, select, textarea, [role="button"], [onclick]';

export function installCardTouch({ card, correctIndicator, incorrectIndicator,
    grade, cycle, feedback, busy, cancelPress = () => {},
    haptic = ms => typeof navigator !== 'undefined' && navigator.vibrate?.(ms),
    getStyle = element => getComputedStyle(element) }) {
    if (card.dataset.touchGesturesInstalled) return;
    card.dataset.touchGesturesInstalled = '1';
    let drag = null;
    let cancelled = false;
    let suppressClickUntil = 0;

    function clearVisuals() {
        card.classList.remove('swiping', 'swipe-commit-correct', 'swipe-commit-incorrect');
        card.style.transform = '';
        card.style.removeProperty?.('--swipe-right');
        card.style.removeProperty?.('--swipe-left');
        correctIndicator.classList.remove('visible', 'dragging');
        incorrectIndicator.classList.remove('visible', 'dragging');
        correctIndicator.style?.removeProperty?.('--swipe-progress');
        incorrectIndicator.style?.removeProperty?.('--swipe-progress');
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
    function updatePosition(touch, event) {
        const prevX = drag.x;
        drag.x = touch.clientX - drag.startX;
        drag.y = touch.clientY - drag.startY;
        if (typeof event?.timeStamp === 'number') {
            const dt = event.timeStamp - drag.lastTime;
            if (dt >= 4 && dt <= 180) {
                const instantVx = (drag.x - prevX) / dt;
                drag.vx = drag.vx ? (drag.vx * 0.35 + instantVx * 0.65) : instantVx;
                drag.lastTime = event.timeStamp;
            } else if (dt > 180) {
                drag.vx = 0;
                drag.lastTime = event.timeStamp;
            }
        }
        drag.maxMovement = Math.max(drag.maxMovement, Math.hypot(drag.x, drag.y));
        const x = Math.abs(drag.x), y = Math.abs(drag.y);
        if (!drag.axis && Math.max(x, y) >= LOCK_DISTANCE) {
            if (x > y * AXIS_LEAD) drag.axis = 'horizontal';
            else if (y > x * AXIS_LEAD) drag.axis = 'vertical';
        }
    }
    function gradeDirection({ allowFlick = false } = {}) {
        if (drag.axis !== 'horizontal' || Math.abs(drag.x) <= Math.abs(drag.y) * AXIS_LEAD) {
            return null;
        }
        const absX = Math.abs(drag.x);
        const isFlick = allowFlick && absX >= FLICK_DISTANCE
            && Math.abs(drag.vx) >= FLICK_VELOCITY
            && Math.sign(drag.vx) === Math.sign(drag.x);
        if (absX < GRADE_DISTANCE && !isFlick) return null;
        return drag.x > 0 ? 'correct' : 'incorrect';
    }
    card.addEventListener('touchstart', event => {
        if (event.touches.length !== 1 || busy()) { cancel(); return; }
        // The set scrubber has its own drag navigation. It keeps ownership.
        if (event.target.closest('.card-back-scrubber')) { cancel(); return; }
        suppressClickUntil = 0;
        cancelled = false;
        card.classList.remove('swipe-rebound');
        const touch = event.touches[0];
        const rect = card.getBoundingClientRect?.();
        const relY = rect?.height > 0 ? ((touch.clientY - rect.top) / rect.height) * 2 - 1 : 0;
        const tiltFactor = Math.max(0.78, Math.min(1.22, 1 - relY * 0.22));
        drag = {
            id: touch.identifier, startX: touch.clientX, startY: touch.clientY,
            x: 0, y: 0, vx: 0, lastTime: typeof event.timeStamp === 'number' ? event.timeStamp : 0,
            tiltFactor, axis: null, maxMovement: 0, committedDirection: null,
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
        updatePosition(touch, event);
        if (drag.maxMovement >= LOCK_DISTANCE) cancelPress();
        // Native vertical scrolling owns scrollports. Outside them, keep
        // the existing vertical content cycling rather than scrolling the page.
        if (drag.axis === 'horizontal' || !drag.scroll) {
            if (event.cancelable) event.preventDefault();
        }
        if (drag.axis !== 'horizontal') return;
        card.classList.add('swiping');
        const dampedY = Math.round(drag.y * DAMPED_Y * 10) / 10;
        const deg = Math.round((drag.x * drag.tiltFactor / 20) * 100) / 100;
        const yPart = dampedY ? ` translateY(${dampedY}px)` : '';
        card.style.transform = `translateX(${drag.x}px)${yPart} rotate(${deg}deg)`
            + (drag.flipped ? ' rotateY(180deg)' : '');
        const horizontalLead = Math.abs(drag.x) > Math.abs(drag.y) * AXIS_LEAD;
        const progress = horizontalLead ? Math.min(1, Math.abs(drag.x) / GRADE_DISTANCE) : 0;
        const rightProgress = drag.x > 0 ? progress : 0;
        const leftProgress = drag.x < 0 ? progress : 0;
        card.style.setProperty?.('--swipe-right', rightProgress.toFixed(3));
        card.style.setProperty?.('--swipe-left', leftProgress.toFixed(3));
        correctIndicator.style?.setProperty?.('--swipe-progress', rightProgress.toFixed(3));
        incorrectIndicator.style?.setProperty?.('--swipe-progress', leftProgress.toFixed(3));
        correctIndicator.classList.toggle('dragging', rightProgress > 0.08);
        incorrectIndicator.classList.toggle('dragging', leftProgress > 0.08);
        const direction = gradeDirection();
        card.classList.toggle('swipe-commit-correct', direction === 'correct');
        card.classList.toggle('swipe-commit-incorrect', direction === 'incorrect');
        correctIndicator.classList.toggle('visible', direction === 'correct');
        incorrectIndicator.classList.toggle('visible', direction === 'incorrect');
        if (direction !== drag.committedDirection) {
            if (direction) haptic(8);
            drag.committedDirection = direction;
        }
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
        updatePosition(touch, event);
        const direction = gradeDirection({ allowFlick: true });
        if (direction && !drag.committedDirection) haptic(8);
        const finished = drag;
        drag = null;
        clearVisuals();
        if (direction) {
            const dampedY = Math.round(finished.y * DAMPED_Y * 10) / 10;
            const deg = Math.round((finished.x * finished.tiltFactor / 20) * 100) / 100;
            card.style.setProperty?.('--swipe-from-x', `${finished.x}px`);
            card.style.setProperty?.('--swipe-from-y', `${dampedY}px`);
            card.style.setProperty?.('--swipe-from-rot', `${deg}deg`);
        } else if (finished.axis === 'horizontal') {
            card.classList.add('swipe-rebound');
            card.addEventListener?.('transitionend', () => card.classList.remove('swipe-rebound'), { once: true });
        }
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
