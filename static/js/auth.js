// ========================================
// 认证相关逻辑（从 index.html 提取）
// ========================================

function switchAuthMode(mode) {
    const loginSection = document.getElementById('loginSection');
    const registerSection = document.getElementById('registerSection');
    const errorDivs = document.querySelectorAll('.form-error');

    errorDivs.forEach(div => div.textContent = '');

    if (mode === 'register') {
        loginSection.style.display = 'none';
        registerSection.style.display = 'block';
    } else {
        loginSection.style.display = 'block';
        registerSection.style.display = 'none';
    }
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');

    errorDiv.textContent = I18n.t('logging_in');

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            location.reload();
        } else {
            const translatedError = I18n.translateError(data.error, 'login_failed');
            errorDiv.textContent = translatedError;
            Modal.toast(translatedError, 'error');
        }
    } catch (error) {
        errorDiv.textContent = I18n.t('network_error');
        Modal.toast(I18n.t('network_error'), 'error');
    }
});


// ========================================
// 发送验证码逻辑
// ========================================
let countdownTimer = null;
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
    btnSendCode.textContent = I18n.t('logging_in').replace('登录', I18n.t('send_code').split(' ')[0]);

    try {
        const response = await fetch('/api/send-verification-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            Modal.toast(I18n.t('code_sent'), 'success');
            codeHint.textContent = I18n.t('code_sent_hint');
            codeHint.style.display = 'block';
            codeHint.style.color = '#28a745';

            // 开始60秒倒计时
            let countdown = 60;
            btnSendCode.textContent = `${countdown}${I18n.t('seconds_retry')}`;

            countdownTimer = setInterval(() => {
                countdown--;
                if (countdown > 0) {
                    btnSendCode.textContent = `${countdown}${I18n.t('seconds_retry')}`;
                } else {
                    clearInterval(countdownTimer);
                    btnSendCode.disabled = false;
                    btnSendCode.textContent = I18n.t('send_code');
                }
            }, 1000);
        } else {
            // 翻译后端错误消息
            const translatedError = I18n.translateError(data.error, 'send_failed');
            Modal.toast(translatedError, 'error');
            btnSendCode.disabled = false;
            btnSendCode.textContent = I18n.t('send_code');
        }
    } catch (error) {
        Modal.toast(I18n.t('network_error'), 'error');
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
        errorDiv.textContent = I18n.t('passwords_not_match');
        Modal.toast(I18n.t('passwords_not_match'), 'warning');
        return;
    }

    if (!verificationCode) {
        errorDiv.textContent = I18n.t('enter_code');
        Modal.toast(I18n.t('enter_code'), 'warning');
        return;
    }

    errorDiv.textContent = I18n.t('registering');

    try {
        const response = await fetch('/api/register', {
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
            errorDiv.textContent = translatedError;
            Modal.toast(translatedError, 'error');
        }
    } catch (error) {
        errorDiv.textContent = I18n.t('network_error');
        Modal.toast(I18n.t('network_error'), 'error');
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

// 打开充值弹窗
if (btnRecharge) {
    btnRecharge.addEventListener('click', () => {
        rechargeModalOverlay.style.display = 'flex';
        // 使用 setTimeout 确保 display 先生效，然后再触发过渡动画
        setTimeout(() => {
            rechargeModalOverlay.classList.add('active');
        }, 10);
    });
}

// 关闭充值弹窗
function closeRechargeModalFunc() {
    rechargeModalOverlay.classList.remove('active');
    // 等待过渡动画结束后隐藏元素
    setTimeout(() => {
        rechargeModalOverlay.style.display = 'none';
    }, 300);
}

if (closeRechargeModal) {
    closeRechargeModal.addEventListener('click', closeRechargeModalFunc);
}

// 点击遮罩关闭
if (rechargeModalOverlay) {
    rechargeModalOverlay.addEventListener('click', (e) => {
        if (e.target === rechargeModalOverlay) {
            closeRechargeModalFunc();
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
            const response = await fetch('/api/redeem', {
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
