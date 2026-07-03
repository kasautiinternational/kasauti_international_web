/* OTP page — 6-box input handling (Kasauti International)
   - digits only, auto-advance, backspace-back, arrow keys
   - full-code paste support
   - combines boxes into hidden #uotp before submit
   - auto-submits when all 6 filled
   - 30s resend cooldown timer                                    */
(function () {
    const inputs = Array.from(document.querySelectorAll('.otp-box'));
    const hidden = document.getElementById('uotp');
    const form   = document.getElementById('otpForm');

    function sync() {
        if (hidden) hidden.value = inputs.map(i => i.value).join('');
        inputs.forEach(i => i.classList.toggle('filled', i.value !== ''));
    }

    function submitForm() {
        if (!form) return;
        setTimeout(function () {
            if (form.requestSubmit) form.requestSubmit();
            else form.submit();
        }, 120);
    }

    inputs.forEach(function (input, idx) {
        input.addEventListener('input', function () {
            input.value = input.value.replace(/\D/g, '').slice(0, 1);
            if (input.value && idx < inputs.length - 1) inputs[idx + 1].focus();
            sync();
            if (inputs.every(i => i.value !== '')) submitForm();
        });

        input.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && !input.value && idx > 0) {
                inputs[idx - 1].focus();
                inputs[idx - 1].value = '';
                sync();
                e.preventDefault();
            }
            if (e.key === 'ArrowLeft'  && idx > 0)                 inputs[idx - 1].focus();
            if (e.key === 'ArrowRight' && idx < inputs.length - 1) inputs[idx + 1].focus();
        });

        input.addEventListener('paste', function (e) {
            e.preventDefault();
            const raw = (e.clipboardData || window.clipboardData).getData('text');
            const data = raw.replace(/\D/g, '').slice(0, inputs.length);
            if (!data) return;
            data.split('').forEach(function (ch, i) { if (inputs[i]) inputs[i].value = ch; });
            const next = Math.min(data.length, inputs.length - 1);
            inputs[next].focus();
            sync();
            if (inputs.every(i => i.value !== '')) submitForm();
        });
    });

    // keep hidden field correct even if user submits via button
    if (form) form.addEventListener('submit', sync);

    // Resend cooldown (30s)
    const resendBtn   = document.getElementById('resendBtn');
    const resendTimer = document.getElementById('resendTimer');
    if (resendBtn && resendTimer) {
        let left = 30;
        const tick = setInterval(function () {
            left -= 1;
            if (left <= 0) {
                clearInterval(tick);
                resendBtn.disabled = false;
                resendTimer.textContent = '';
            } else {
                resendTimer.textContent = '(' + left + 's)';
            }
        }, 1000);
    }
})();
