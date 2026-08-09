// ========================================
// 认证相关逻辑（从 index.html 提取）
// ========================================

const authModalOverlay = document.getElementById('authModalOverlay');
const closeAuthModalButton = document.getElementById('closeAuthModal');
const btnGuestLogin = document.getElementById('btnGuestLogin');
const btnGuestRegister = document.getElementById('btnGuestRegister');
let authModalReturnFocus = null;
let authModalPreviousOverflow = '';

function getAuthFocusableElements() {
    if (!authModalOverlay) return [];
    return Array.from(authModalOverlay.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )).filter(element => element.offsetParent !== null && !element.hidden);
}

function openAuthModal(mode = 'login') {
    if (!authModalOverlay || window.IS_AUTHENTICATED) return;
    if (typeof window.saveGuestDraft === 'function') window.saveGuestDraft();
    switchAuthMode(mode);
    if (!authModalOverlay.classList.contains('auth-modal-show')) {
        authModalReturnFocus = document.activeElement;
        authModalPreviousOverflow = document.body.style.overflow;
    }
    authModalOverlay.classList.add('auth-modal-show');
    authModalOverlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    window.setTimeout(() => {
        const target = mode === 'register'
            ? document.getElementById('regUsername')
            : document.getElementById('loginUsername');
        (target || getAuthFocusableElements()[0])?.focus();
    }, 50);
}

function closeAuthModal() {
    if (!authModalOverlay?.classList.contains('auth-modal-show')) return;
    authModalOverlay.classList.remove('auth-modal-show');
    authModalOverlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = authModalPreviousOverflow;
    const returnFocus = authModalReturnFocus;
    authModalReturnFocus = null;
    if (returnFocus?.isConnected) returnFocus.focus();
}

window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;

btnGuestLogin?.addEventListener('click', () => openAuthModal('login'));
btnGuestRegister?.addEventListener('click', () => openAuthModal('register'));
closeAuthModalButton?.addEventListener('click', closeAuthModal);

authModalOverlay?.addEventListener('click', event => {
    if (event.target === authModalOverlay) closeAuthModal();
});

authModalOverlay?.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
        event.preventDefault();
        closeAuthModal();
        return;
    }
    if (event.key !== 'Tab') return;
    const focusable = getAuthFocusableElements();
    if (focusable.length === 0) {
        event.preventDefault();
        authModalOverlay.focus();
        return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
});

function setTranslatedStatus(element, key, fallbackKey = '') {
    element.dataset.i18nStatusKey = key || '';
    element.dataset.i18nStatusFallback = fallbackKey;
    element.textContent = fallbackKey ? I18n.translateError(key, fallbackKey) : I18n.t(key);
}

function clearTranslatedStatus(element) {
    element.textContent = '';
    delete element.dataset.i18nStatusKey;
    delete element.dataset.i18nStatusFallback;
}

function switchAuthMode(mode) {
    const loginSection = document.getElementById('loginSection');
    const registerSection = document.getElementById('registerSection');
    const errorDivs = document.querySelectorAll('.form-error');

    errorDivs.forEach(clearTranslatedStatus);

    if (mode === 'register') {
        loginSection.style.display = 'none';
        registerSection.style.display = 'block';
    } else {
        loginSection.style.display = 'block';
        registerSection.style.display = 'none';
    }

    if (authModalOverlay?.classList.contains('auth-modal-show')) {
        window.setTimeout(() => {
            const target = mode === 'register'
                ? document.getElementById('regUsername')
                : document.getElementById('loginUsername');
            target?.focus();
        }, 0);
    }
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');

    setTranslatedStatus(errorDiv, 'logging_in');

    try {
        const response = await window.apiFetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            location.reload();
        } else {
            const translatedError = I18n.translateError(data.error, 'login_failed');
            setTranslatedStatus(errorDiv, data.error, 'login_failed');
            Modal.toast(translatedError, 'error');
        }
    } catch (error) {
        setTranslatedStatus(errorDiv, 'network_error');
        Modal.toast(I18n.t('network_error'), 'error');
    }
});


// ========================================
// 发送验证码逻辑
// ========================================
let countdownTimer = null;
let countdownRemaining = null;
let isSendingCode = false;
const btnSendCode = document.getElementById('btnSendCode');
const regEmail = document.getElementById('regEmail');
const codeHint = document.getElementById('codeHint');

btnSendCode.addEventListener('click', async () => {
    const email = regEmail.value.trim();

    if (!email) {
        Modal.toast(I18n.t('enter_email_first'), 'warning');
        regEmail.focus();
        return;
    }

    // 简单的邮箱格式验证
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailPattern.test(email)) {
        Modal.toast(I18n.t('invalid_email'), 'warning');
        regEmail.focus();
        return;
    }

    btnSendCode.disabled = true;
    isSendingCode = true;
    btnSendCode.textContent = I18n.t('sending_code');

    try {
        const response = await window.apiFetch('/api/send-verification-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            isSendingCode = false;
            Modal.toast(I18n.t('code_sent'), 'success');
            codeHint.textContent = I18n.t('code_sent_hint');
            codeHint.style.display = 'block';
            codeHint.style.color = '#28a745';

            // 开始60秒倒计时
            countdownRemaining = 60;
            btnSendCode.textContent = `${countdownRemaining}${I18n.t('seconds_retry')}`;

            countdownTimer = setInterval(() => {
                countdownRemaining--;
                if (countdownRemaining > 0) {
                    btnSendCode.textContent = `${countdownRemaining}${I18n.t('seconds_retry')}`;
                } else {
                    clearInterval(countdownTimer);
                    countdownRemaining = null;
                    btnSendCode.disabled = false;
                    btnSendCode.textContent = I18n.t('send_code');
                }
            }, 1000);
        } else {
            // 翻译后端错误消息
            const translatedError = I18n.translateError(data.error, 'send_failed');
            Modal.toast(translatedError, 'error');
            isSendingCode = false;
            countdownRemaining = null;
            btnSendCode.disabled = false;
            btnSendCode.textContent = I18n.t('send_code');
        }
    } catch (error) {
        Modal.toast(I18n.t('network_error'), 'error');
        isSendingCode = false;
        countdownRemaining = null;
        btnSendCode.disabled = false;
        btnSendCode.textContent = I18n.t('send_code');
    }
});

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value.trim();
    const verificationCode = document.getElementById('regVerificationCode').value.trim();
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    const errorDiv = document.getElementById('registerError');

    if (password !== confirmPassword) {
        setTranslatedStatus(errorDiv, 'passwords_not_match');
        Modal.toast(I18n.t('passwords_not_match'), 'warning');
        return;
    }

    if (!verificationCode) {
        setTranslatedStatus(errorDiv, 'enter_code');
        Modal.toast(I18n.t('enter_code'), 'warning');
        return;
    }

    setTranslatedStatus(errorDiv, 'registering');

    try {
        const response = await window.apiFetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, verification_code: verificationCode })
        });

        const data = await response.json();

        if (response.ok) {
            await Modal.alert(I18n.t('register_success'), I18n.t('register_success_msg'), 'success');
            switchAuthMode('login');
            document.getElementById('loginUsername').value = username;
            document.getElementById('loginPassword').focus();
        } else {
            const translatedError = I18n.translateError(data.error, 'register_failed');
            setTranslatedStatus(errorDiv, data.error, 'register_failed');
            Modal.toast(translatedError, 'error');
        }
    } catch (error) {
        setTranslatedStatus(errorDiv, 'network_error');
        Modal.toast(I18n.t('network_error'), 'error');
    }
});

I18n.onLangChange(() => {
    document.querySelectorAll('[data-i18n-status-key]').forEach(element => {
        const key = element.dataset.i18nStatusKey;
        const fallbackKey = element.dataset.i18nStatusFallback;
        element.textContent = fallbackKey ? I18n.translateError(key, fallbackKey) : I18n.t(key);
    });

    if (codeHint.style.display !== 'none') codeHint.textContent = I18n.t('code_sent_hint');
    if (isSendingCode) btnSendCode.textContent = I18n.t('sending_code');
    else if (countdownRemaining !== null) {
        btnSendCode.textContent = `${countdownRemaining}${I18n.t('seconds_retry')}`;
    } else {
        btnSendCode.textContent = I18n.t('send_code');
    }
});

// ========================================
// 充值模态框逻辑
// ========================================
const rechargeModalOverlay = document.getElementById('rechargeModalOverlay');
const btnRecharge = document.getElementById('btnRecharge');
const closeRechargeModal = document.getElementById('closeRechargeModal');
const btnRedeem = document.getElementById('btnRedeem');
const cardKeyInput = document.getElementById('cardKeyInput');
let rechargeReturnFocus = null;
let rechargeOpenTimer = null;
let rechargeCloseTimer = null;
let rechargeClosing = false;

function getRechargeFocusableElements() {
    if (!rechargeModalOverlay) return [];
    const selector = [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled]):not([type="hidden"])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])'
    ].join(',');
    return Array.from(rechargeModalOverlay.querySelectorAll(selector)).filter(element => (
        !element.hidden && element.getAttribute('aria-hidden') !== 'true'
    ));
}

function openRechargeModalFunc() {
    if (!rechargeModalOverlay) return;
    const wasHidden = rechargeModalOverlay.style.display === 'none';
    window.clearTimeout(rechargeOpenTimer);
    window.clearTimeout(rechargeCloseTimer);
    if (wasHidden || !rechargeReturnFocus?.isConnected) rechargeReturnFocus = document.activeElement;
    rechargeClosing = false;
    rechargeModalOverlay.style.display = 'flex';
    rechargeOpenTimer = window.setTimeout(() => {
        rechargeModalOverlay.classList.add('active');
        (closeRechargeModal || getRechargeFocusableElements()[0])?.focus();
    }, 10);
}

// 打开充值弹窗
if (btnRecharge) {
    btnRecharge.addEventListener('click', openRechargeModalFunc);
}

// 关闭充值弹窗
function closeRechargeModalFunc() {
    if (!rechargeModalOverlay || rechargeClosing || rechargeModalOverlay.style.display === 'none') return;
    rechargeClosing = true;
    window.clearTimeout(rechargeOpenTimer);
    rechargeModalOverlay.classList.remove('active');
    const returnFocus = rechargeReturnFocus;
    rechargeCloseTimer = window.setTimeout(() => {
        rechargeModalOverlay.style.display = 'none';
        rechargeClosing = false;
        rechargeReturnFocus = null;
        if (returnFocus?.isConnected) returnFocus.focus();
    }, 300);
}

if (closeRechargeModal) {
    closeRechargeModal.addEventListener('click', closeRechargeModalFunc);
}

// 点击遮罩关闭
if (rechargeModalOverlay) {
    rechargeModalOverlay.tabIndex = -1;
    rechargeModalOverlay.addEventListener('click', (e) => {
        if (e.target === rechargeModalOverlay) {
            closeRechargeModalFunc();
        }
    });

    rechargeModalOverlay.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            closeRechargeModalFunc();
            return;
        }

        if (e.key !== 'Tab') return;
        const focusable = getRechargeFocusableElements();
        if (focusable.length === 0) {
            e.preventDefault();
            rechargeModalOverlay.focus();
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const activeElement = document.activeElement;
        if (e.shiftKey && (activeElement === first || !rechargeModalOverlay.contains(activeElement))) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && (activeElement === last || !rechargeModalOverlay.contains(activeElement))) {
            e.preventDefault();
            first.focus();
        }
    });
}

// 使用卡密充值
if (btnRedeem) {
    btnRedeem.addEventListener('click', async () => {
        const code = cardKeyInput.value.trim();

        if (!code) {
            Modal.toast(I18n.t('enter_card_key_msg'), 'warning');
            cardKeyInput.focus();
            return;
        }

        btnRedeem.disabled = true;
        btnRedeem.textContent = I18n.t('recharging');

        try {
            const response = await window.apiFetch('/api/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (response.ok) {
                // 使用翻译后的成功消息，格式：充值成功！用户现有 X 点
                const successMsg = I18n.t('recharge_success_msg').replace('{0}', data.new_credits);
                Modal.toast(successMsg, 'success');
                // 更新点数显示
                const creditEl = document.getElementById('userCredits');
                if (creditEl) {
                    creditEl.innerHTML = `🪙 ${data.new_credits} <span data-i18n="credits_label">${I18n.t('credits_label')}</span>`;
                }
                // 关闭弹窗并清空输入
                cardKeyInput.value = '';
                closeRechargeModalFunc();
            } else {
                Modal.toast(I18n.translateError(data.error, 'recharge_failed'), 'error');
            }
        } catch (error) {
            Modal.toast(I18n.t('network_error'), 'error');
        } finally {
            btnRedeem.disabled = false;
            btnRedeem.textContent = I18n.t('confirm_recharge');
        }
    });
}

// 回车提交卡密
if (cardKeyInput) {
    cardKeyInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            btnRedeem.click();
        }
    });
}
