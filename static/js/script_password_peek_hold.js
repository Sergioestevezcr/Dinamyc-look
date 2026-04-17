function attachPressHoldPeek(container) {
    const passwordInputs = container.querySelectorAll('input[type="password"]');

    passwordInputs.forEach((input) => {
        if (input.dataset.peekBound === '1') {
            return;
        }

        input.dataset.peekBound = '1';

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-peek-btn';
        btn.setAttribute('aria-label', 'Mantén presionado para ver contraseña');
        btn.innerHTML = '<i class="bx bx-show"></i>';

        const reveal = () => {
            input.type = 'text';
            btn.classList.add('is-peeking');
        };

        const hide = () => {
            input.type = 'password';
            btn.classList.remove('is-peeking');
        };

        btn.addEventListener('mousedown', reveal);
        btn.addEventListener('mouseup', hide);
        btn.addEventListener('mouseleave', hide);

        btn.addEventListener('touchstart', reveal, { passive: true });
        btn.addEventListener('touchend', hide);
        btn.addEventListener('touchcancel', hide);

        btn.addEventListener('keydown', (event) => {
            if (event.key === ' ' || event.key === 'Enter') {
                reveal();
            }
        });

        btn.addEventListener('keyup', (event) => {
            if (event.key === ' ' || event.key === 'Enter') {
                hide();
            }
        });

        btn.addEventListener('blur', hide);

        if (input.parentElement) {
            input.parentElement.appendChild(btn);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    attachPressHoldPeek(document);
});
