// ========================================
// 管理后台逻辑（从 admin.html 提取）
// ========================================

let users = [];
let currentSessions = []; // Store current user sessions (list only)
let currentViewUserId = null; // Track which user's sessions are being viewed
let usersLoadGeneration = 0;
let sessionViewGeneration = 0;
let sessionDetailGeneration = 0;
let sessionListController = null;
let sessionDetailController = null;

function apiFetch(url, options = {}) {
    const requestOptions = { ...options };
    const method = (requestOptions.method || 'GET').toUpperCase();
    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
        const headers = new Headers(requestOptions.headers || {});
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken) headers.set('X-CSRFToken', csrfToken);
        requestOptions.headers = headers;
    }
    return fetch(url, requestOptions);
}

function escapeHtml(value) {
    const element = document.createElement('div');
    element.textContent = value ?? '';
    return element.innerHTML;
}

// 加载用户数据
async function loadUsers() {
    const generation = ++usersLoadGeneration;
    try {
        const response = await apiFetch('/api/admin/users');
        if (generation !== usersLoadGeneration) return;
        if (response.ok) {
            const loadedUsers = await response.json();
            if (generation !== usersLoadGeneration) return;
            users = loadedUsers;
            renderUsers();
            updateStats();
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else if (response.status === 403) {
            await Modal.alert(I18n.t('permission_error'), I18n.t('no_admin_permission'), 'error');
            window.location.href = '/';
        }
    } catch (error) {
        if (generation !== usersLoadGeneration) return;
        console.error('Load users failed:', error);
        Modal.toast(I18n.t('load_users_failed'), 'error');
    }
}

// 渲染用户表格
function renderUsers() {
    const tbody = document.getElementById('userTableBody');
    if (users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty-cell">${I18n.t('no_users')}</td></tr>`;
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr class="${user.is_admin ? 'admin-row' : ''}">
            <td>${escapeHtml(user.id)}</td>
            <td>
                <span class="username">${escapeHtml(user.username)}</span>
                ${user.username === 'admin' ? `<span class="badge badge-primary">${I18n.t('main_admin')}</span>` : ''}
            </td>
            <td>
                <span class="badge ${user.is_admin ? 'badge-admin' : 'badge-user'}">
                    ${user.is_admin ? I18n.t('admin') : I18n.t('normal_user')}
                </span>
            </td>
            <td>${user.credits !== undefined ? user.credits : '-'}</td>
            <td>${user.session_count || 0}</td>
            <td>${user.message_count || 0}</td>
            <td>${formatDate(user.created_at)}</td>
            <td class="action-cell">
                <button class="btn-action btn-view" onclick="viewSessions(${Number(user.id)})">
                    ${I18n.t('view_sessions')}
                </button>
                ${user.username !== 'admin' ? `
                    <button class="btn-action btn-toggle" onclick="toggleAdmin(${Number(user.id)})">
                        ${user.is_admin ? I18n.t('revoke_admin') : I18n.t('set_admin')}
                    </button>
                    <button class="btn-action btn-view" onclick="addCredits(${Number(user.id)})">
                        ${I18n.t('add_credits')}
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteUser(${Number(user.id)})">
                        ${I18n.t('delete_user')}
                    </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

// 更新统计数据
function updateStats() {
    document.getElementById('totalUsers').textContent = users.length;
    document.getElementById('totalSessions').textContent = users.reduce((sum, u) => sum + (u.session_count || 0), 0);
    document.getElementById('totalMessages').textContent = users.reduce((sum, u) => sum + (u.message_count || 0), 0);
    document.getElementById('totalAdmins').textContent = users.filter(u => u.is_admin).length;
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    // 根据当前语言选择日期格式
    const locale = I18n.getLang() === 'zh' ? 'zh-CN' : 'en-US';
    return date.toLocaleString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatLocalDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 查看用户会话
async function viewSessions(userId) {
    const viewUserId = userId;
    const generation = ++sessionViewGeneration;
    sessionDetailGeneration++;
    sessionListController?.abort();
    sessionDetailController?.abort();
    sessionListController = new AbortController();
    const username = users.find(user => user.id === userId)?.username || '';
    document.getElementById('modalTitle').textContent = `${username} - ${I18n.t('session_detail')}`;
    document.getElementById('sessionModal').hidden = false;
    currentViewUserId = viewUserId;

    // Reset UI
    const sidebarList = document.getElementById('sessionSidebarList');
    const mainContent = document.getElementById('sessionMainContent');
    sidebarList.innerHTML = `<div style="padding:10px; color:var(--text-muted)">${I18n.t('loading')}</div>`;
    mainContent.innerHTML = '';

    try {
        const response = await apiFetch(`/api/admin/users/${viewUserId}/sessions`, {
            signal: sessionListController.signal
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const sessions = await response.json();
        if (generation !== sessionViewGeneration || currentViewUserId !== viewUserId) return;
        currentSessions = sessions;

        if (currentSessions.length === 0) {
            sidebarList.innerHTML = `<div style="padding:10px; color:var(--text-muted)">${I18n.t('no_sessions')}</div>`;
            renderEmptyState();
            return;
        }

        renderSessionList();
        // Select first session by default
        if (currentSessions.length > 0) {
            selectSession(currentSessions[0].id);
        }

    } catch (error) {
        if (error.name === 'AbortError' || generation !== sessionViewGeneration) return;
        sidebarList.innerHTML = `<div style="padding:10px; color:var(--error)">${I18n.t('load_sessions_failed')}</div>`;
        Modal.toast(I18n.t('load_sessions_failed'), 'error');
    }
}

function renderSessionList() {
    const sidebarList = document.getElementById('sessionSidebarList');
    sidebarList.innerHTML = currentSessions.map(session => {
        // 翻译会话标题（如果是默认的"新对话"）
        const title = session.title === '新对话' ? I18n.t('new_chat') : session.title;
        return `
        <button type="button" class="session-list-item" id="session-item-${escapeHtml(session.id)}"
            data-session-id="${escapeHtml(session.id)}">
            <div class="session-list-item-title">${escapeHtml(title)}</div>
            <div class="session-list-item-date">${formatDate(session.updated_at)} · ${session.message_count || 0} ${I18n.t('messages_count')}</div>
        </button>
    `}).join('');
    sidebarList.querySelectorAll('.session-list-item').forEach(item => {
        item.addEventListener('click', () => selectSession(item.dataset.sessionId));
    });
}

async function selectSession(sessionId) {
    const viewUserId = currentViewUserId;
    const generation = sessionViewGeneration;
    const detailGeneration = ++sessionDetailGeneration;
    sessionDetailController?.abort();
    const controller = new AbortController();
    sessionDetailController = controller;
    // Update active state in sidebar
    document.querySelectorAll('.session-list-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.getElementById(`session-item-${sessionId}`);
    if (activeItem) activeItem.classList.add('active');

    const mainContent = document.getElementById('sessionMainContent');

    // 从服务器加载单个会话的消息
    mainContent.innerHTML = `<div class="viewer-empty"><div class="viewer-empty-icon">⏳</div><p>${I18n.t('loading')}</p></div>`;

    try {
        const response = await apiFetch(`/api/admin/users/${viewUserId}/sessions/${encodeURIComponent(sessionId)}`, {
            signal: controller.signal
        });
        if (generation !== sessionViewGeneration || detailGeneration !== sessionDetailGeneration
            || currentViewUserId !== viewUserId) return;
        if (!response.ok) {
            mainContent.innerHTML = `<div class="viewer-empty"><div class="viewer-empty-icon">❌</div><p>${I18n.t('load_sessions_failed')}</p></div>`;
            return;
        }
        const session = await response.json();
        if (generation !== sessionViewGeneration || detailGeneration !== sessionDetailGeneration
            || currentViewUserId !== viewUserId) return;

        if (!session.messages || session.messages.length === 0) {
            mainContent.innerHTML = `
                <div class="viewer-empty">
                    <div class="viewer-empty-icon">💬</div>
                    <p>${I18n.t('no_messages')}</p>
                </div>
            `;
            return;
        }

        mainContent.innerHTML = session.messages.map(msg => {
            const roleClass = msg.role === 'user' ? 'user' : 'assistant';
            return `
            <div class="viewer-message ${roleClass}">
                <div class="viewer-avatar">${msg.role === 'user' ? '👤' : '🤖'}</div>
                <div class="viewer-content-wrapper">
                     <div class="viewer-bubble">
                        ${escapeHtml(msg.content || '')}
                        ${msg.image ? `<img src="${escapeHtml(msg.thumbnail || msg.image)}" data-image-src="${escapeHtml(msg.image)}" class="viewer-image" alt="${I18n.t('generated_image')}">` : ''}
                    </div>
                     <!-- Reference Images -->
                     ${msg.reference_images ? `
                        <div style="margin-top: 5px; display: flex; gap: 5px; flex-wrap: wrap;">
                            ${msg.reference_images.map(ref => `
                                <img src="/static/images/${escapeHtml(ref)}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover; border: 1px solid rgba(255,255,255,0.1);">
                            `).join('')}
                        </div>
                     ` : ''}
                </div>
            </div>`;
        }).join('');

        mainContent.querySelectorAll('.viewer-image').forEach(image => {
            image.addEventListener('click', () => openImagePreview(image.dataset.imageSrc));
        });

        // Scroll to bottom
        setTimeout(() => {
            mainContent.scrollTop = mainContent.scrollHeight;
        }, 0);

    } catch (error) {
        if (error.name === 'AbortError' || generation !== sessionViewGeneration
            || detailGeneration !== sessionDetailGeneration) return;
        mainContent.innerHTML = `<div class="viewer-empty"><div class="viewer-empty-icon">❌</div><p>${I18n.t('load_sessions_failed')}</p></div>`;
    }
}

function renderEmptyState() {
    const mainContent = document.getElementById('sessionMainContent');
    mainContent.innerHTML = `
        <div class="viewer-empty">
            <div class="viewer-empty-icon">📂</div>
            <p>${I18n.t('select_session')}</p>
        </div>
    `;
}

// 关闭会话模态框
function closeSessionModal() {
    document.getElementById('sessionModal').hidden = true;
    sessionViewGeneration++;
    sessionDetailGeneration++;
    sessionListController?.abort();
    sessionDetailController?.abort();
    currentViewUserId = null;
}

// 切换管理员状态
async function toggleAdmin(userId) {
    try {
        const response = await apiFetch(`/api/admin/users/${userId}/toggle-admin`, {
            method: 'POST'
        });
        const data = await response.json();
        if (response.ok) {
            Modal.toast(I18n.t('operation_success'), 'success');
            loadUsers();
        } else {
            Modal.alert(I18n.t('operation_failed'), I18n.translateError(data.error, 'unknown_error'), 'error');
        }
    } catch (error) {
        Modal.alert(I18n.t('network_error'), I18n.t('connect_error'), 'error');
    }
}

// 删除用户
async function deleteUser(userId) {
    const username = users.find(user => user.id === userId)?.username || '';
    const confirmed = await Modal.confirm(I18n.t('delete_user'), I18n.t('confirm_delete_user', username), 'warning');
    if (!confirmed) {
        return;
    }

    try {
        const response = await apiFetch(`/api/admin/users/${userId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (response.ok) {
            Modal.toast(I18n.t('user_deleted', username), 'success');
            loadUsers();
        } else {
            Modal.alert(I18n.t('delete_failed'), I18n.translateError(data.error, 'unknown_error'), 'error');
        }
    } catch (error) {
        Modal.alert(I18n.t('network_error'), I18n.t('connect_error'), 'error');
    }
}

// 给用户充值
async function addCredits(userId) {
    const username = users.find(user => user.id === userId)?.username || '';
    const amountStr = await Modal.prompt(I18n.t('credits_recharge'), I18n.t('credits_recharge_prompt', username), '10');
    if (amountStr === null) return;

    const amount = parseInt(amountStr);
    if (isNaN(amount) || amount === 0) {
        Modal.toast(I18n.t('invalid_number'), 'warning');
        return;
    }

    try {
        const response = await apiFetch(`/api/admin/users/${userId}/credits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });
        const data = await response.json();

        if (response.ok) {
            await Modal.alert(I18n.t('recharge_success'), I18n.t('recharge_success_msg', data.new_credits), 'success');
            loadUsers();
        } else {
            Modal.alert(I18n.t('recharge_failed'), I18n.translateError(data.error, 'operation_failed'), 'error');
        }
    } catch (error) {
        Modal.alert(I18n.t('network_error'), I18n.t('connect_error'), 'error');
    }
}

// ========================================
// 数据清理功能
// ========================================

async function cleanupData(days) {
    const confirmed = await Modal.confirm(I18n.t('confirm_cleanup'), I18n.t('confirm_cleanup_msg', days), 'warning');
    if (!confirmed) {
        return;
    }

    const date = new Date();
    date.setDate(date.getDate() - days);
    const cutoffDate = formatLocalDate(date);

    await performCleanup(cutoffDate);
}

async function cleanupAllData() {
    const confirmed = await Modal.confirm(
        I18n.t('cleanup_all_title'),
        I18n.t('cleanup_all_msg'),
        'warning'
    );
    if (!confirmed) {
        return;
    }

    // 用明天的日期作为截止日期，确保所有数据都被清理
    const date = new Date();
    date.setDate(date.getDate() + 1);
    const cutoffDate = formatLocalDate(date);

    await performCleanup(cutoffDate);
}

async function cleanupDataCustom() {
    const dateInput = document.getElementById('cleanupDate');
    const cutoffDate = dateInput.value;

    if (!cutoffDate) {
        Modal.toast(I18n.t('select_date'), 'warning');
        return;
    }

    const confirmed = await Modal.confirm(I18n.t('custom_cleanup'), I18n.t('custom_cleanup_msg', cutoffDate), 'warning');
    if (!confirmed) {
        return;
    }

    await performCleanup(cutoffDate);
}

async function performCleanup(cutoffDate) {
    try {
        const response = await apiFetch('/api/admin/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cutoff_date: cutoffDate })
        });

        const data = await response.json();

        if (response.ok) {
            const stats = data.deleted_stats;
            let message = `${I18n.t('cleanup_complete')}!\n${I18n.t('cleanup_messages')}: ${stats.messages}\n${I18n.t('cleanup_images')}: ${stats.images}\n${I18n.t('cleanup_sessions')}: ${stats.sessions}`;
            if (stats.orphan_images > 0 || stats.orphan_thumbnails > 0) {
                message += `\n\n${I18n.t('orphan_files')}:\n- ${I18n.t('cleanup_images')}: ${stats.orphan_images}\n- ${I18n.t('cleanup_thumbnails')}: ${stats.orphan_thumbnails}`;
            }
            await Modal.alert(I18n.t('cleanup_complete'), message, 'success');
            loadUsers();
        } else {
            Modal.alert(I18n.t('cleanup_failed'), I18n.translateError(data.error, 'operation_failed'), 'error');
        }
    } catch (error) {
        Modal.alert(I18n.t('network_error'), I18n.t('connect_error'), 'error');
    }
}

// ========================================
// 图片预览功能
// ========================================

function openImagePreview(imageSrc) {
    const modal = document.getElementById('adminImageModal');
    const img = document.getElementById('adminModalImage');
    const downloadBtn = document.getElementById('adminBtnDownload');

    img.src = imageSrc;
    downloadBtn.href = imageSrc;
    modal.hidden = false;
}

function closeImagePreview() {
    document.getElementById('adminImageModal').hidden = true;
}

// ========================================
// 卡密管理功能
// ========================================
let cardKeys = [];

async function loadCardKeys() {
    try {
        const response = await apiFetch('/api/admin/card-keys');
        if (response.ok) {
            cardKeys = await response.json();
            renderCardKeys();
        }
    } catch (error) {
        console.error('加载卡密失败:', error);
    }
}

function renderCardKeys() {
    const tbody = document.getElementById('cardKeyTableBody');
    if (cardKeys.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">${I18n.t('no_cards')}</td></tr>`;
        return;
    }

    tbody.innerHTML = cardKeys.map(key => `
        <tr class="${key.is_used ? 'used-row' : ''}">
            <td>
                <code class="card-key-code">${key.code_prefix}****-****-****</code>
            </td>
            <td><span class="credits-badge">🪙 ${key.credits}</span></td>
            <td>
                <span class="badge ${key.is_used ? 'badge-used' : 'badge-available'}">
                    ${key.is_used ? I18n.t('used') : I18n.t('available')}
                </span>
            </td>
            <td>${escapeHtml(key.used_by_username || '-')}</td>
            <td>${formatDate(key.created_at)}</td>
            <td>-</td>
        </tr>
    `).join('');
}

async function generateCardKeys() {
    const credits = parseInt(document.getElementById('cardKeyCredits').value);
    const count = parseInt(document.getElementById('cardKeyCount').value);

    if (isNaN(credits) || credits <= 0) {
        Modal.toast(I18n.t('invalid_credits'), 'warning');
        return;
    }
    if (isNaN(count) || count <= 0 || count > 100) {
        Modal.toast(I18n.t('credits_must_range'), 'warning');
        return;
    }

    try {
        const response = await apiFetch('/api/admin/card-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credits, count })
        });

        const data = await response.json();

        if (response.ok) {
            await Modal.generatedKeys(
                I18n.t('keys_generated'),
                I18n.t('save_keys_warning'),
                data.keys.map(key => key.code),
                I18n.t('copy'),
                I18n.t('copied'),
                I18n.t('copy_failed')
            );
            loadCardKeys();
        } else {
            Modal.alert(I18n.t('generate_failed_msg'), I18n.translateError(data.error, 'operation_failed'), 'error');
        }
    } catch (error) {
        Modal.alert(I18n.t('network_error'), I18n.t('connect_error'), 'error');
    }
}

function copyCardKey(code) {
    navigator.clipboard.writeText(code).then(() => {
        Modal.toast(I18n.t('key_copied'), 'success');
    }).catch(() => {
        Modal.toast(I18n.t('copy_failed'), 'error');
    });
}

// ========================================
// Flatpickr 日期选择器初始化
// ========================================
let datePicker = null;

function initDatePicker() {
    const dateInput = document.getElementById('cleanupDate');
    if (!dateInput) return;

    // 如果已存在实例，先销毁
    if (datePicker) {
        datePicker.destroy();
    }

    // 初始化 Flatpickr
    datePicker = flatpickr(dateInput, {
        locale: I18n.getLang() === 'zh' ? 'zh' : 'default',
        dateFormat: 'Y-m-d',
        maxDate: 'today',
        disableMobile: true,  // 禁用移动端原生选择器，统一使用 Flatpickr
        theme: 'dark'
    });
}

function refreshOpenSessionModal() {
    const modal = document.getElementById('sessionModal');
    if (currentViewUserId === null || modal?.hidden) return;

    const username = users.find(user => user.id === currentViewUserId)?.username || '';
    document.getElementById('modalTitle').textContent = `${username} - ${I18n.t('session_detail')}`;

    const activeSessionId = document.querySelector('#sessionSidebarList .session-list-item.active')?.dataset.sessionId;
    if (currentSessions.length === 0) {
        document.getElementById('sessionSidebarList').innerHTML =
            `<div style="padding:10px; color:var(--text-muted)">${I18n.t('no_sessions')}</div>`;
        renderEmptyState();
        return;
    }

    renderSessionList();
    if (activeSessionId) selectSession(activeSessionId);
}

// 监听语言切换
I18n.onLangChange(() => {
    initDatePicker();
    // 重新渲染用户表格和卡密表格以更新翻译
    renderUsers();
    renderCardKeys();
    loadApiSettings();
    if (!document.getElementById('pricingModal')?.hidden) openPricingModal();
    refreshOpenSessionModal();
});

// ========================================
// API 设置功能
// ========================================

window.currentApiSettings = {};

async function loadApiSettings() {
    try {
        const response = await apiFetch('/api/admin/api-settings');
        if (!response.ok) return;
        const data = await response.json();
        window.currentApiSettings = data;

        const dot = document.getElementById('apiStatusDot');
        const text = document.getElementById('apiStatusText');
        const badge = document.getElementById('apiSourceBadge');

        if (data.configured) {
            dot.className = 'status-dot status-connected';
            text.textContent = I18n.t('api_configured');

            // 填充表单
            document.getElementById('apiProvider').value = data.provider;
            document.getElementById('apiKeyInput').value = '';
            document.getElementById('apiKeyInput').placeholder = data.api_key_masked || '****';
            if (data.custom_base_url) {
                document.getElementById('customBaseUrl').value = data.custom_base_url;
            }
            if (data.default_model) {
                document.getElementById('defaultModel').value = data.default_model;
            }
            if (data.email_sender) {
                document.getElementById('emailSender').value = data.email_sender;
            }
            const emailPasswordInput = document.getElementById('emailPassword');
            emailPasswordInput.value = '';
            if (data.email_password_configured) emailPasswordInput.placeholder = '********';
            if (data.smtp_server) {
                document.getElementById('smtpServer').value = data.smtp_server;
            }
            if (data.smtp_port) {
                document.getElementById('smtpPort').value = data.smtp_port;
            }
            toggleProviderFields();

            // 显示数据来源
            if (data.source === 'env') {
                badge.textContent = I18n.t('from_env');
                badge.hidden = false;
            } else {
                badge.hidden = true;
            }
        } else {
            dot.className = 'status-dot status-disconnected';
            text.textContent = I18n.t('api_not_configured');
            badge.hidden = true;
        }
    } catch (error) {
        console.error('加载 API 设置失败:', error);
    }
}

function toggleProviderFields() {
    const provider = document.getElementById('apiProvider').value;
    const customGroup = document.getElementById('customUrlGroup');

    customGroup.style.display = provider === 'custom' ? 'block' : 'none';
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('apiKeyInput');
    const icon = document.getElementById('visibilityIcon');
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = '🔒';
    } else {
        input.type = 'password';
        icon.textContent = '👁️';
    }
}

async function saveApiSettings() {
    const provider = document.getElementById('apiProvider').value;
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    const customBaseUrl = document.getElementById('customBaseUrl').value.trim();
    const defaultModel = document.getElementById('defaultModel').value;
    const emailSender = document.getElementById('emailSender').value.trim();
    const emailPassword = document.getElementById('emailPassword').value.trim();
    const smtpServer = document.getElementById('smtpServer').value.trim();
    const smtpPort = document.getElementById('smtpPort').value.trim();

    // 如果尚未配置任何 API，必须填写。如果已经配置过，可以传空，后端会复用原有配置
    if (!apiKey && (!window.currentApiSettings?.configured || window.currentApiSettings?.source === 'env')) {
        Modal.toast(I18n.t('api_key_required'), 'warning');
        return false;
    }

    if (provider === 'custom' && !customBaseUrl) {
        Modal.toast(I18n.t('custom_url_required'), 'warning');
        return false;
    }

    try {
        const response = await apiFetch('/api/admin/api-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider,
                api_key: apiKey,
                custom_base_url: provider === 'custom' ? customBaseUrl : null,
                default_model: defaultModel,
                email_sender: emailSender || null,
                email_password: emailPassword || null,
                smtp_server: smtpServer || null,
                smtp_port: smtpPort ? parseInt(smtpPort) : null
            })
        });

        const data = await response.json();

        if (response.ok) {
            Modal.toast(I18n.t('api_settings_saved'), 'success');
            // 重新加载设置以更新显示
            loadApiSettings();
            return true;
        } else {
            Modal.alert(
                I18n.t('save_failed'),
                I18n.translateError(data.error, 'operation_failed'),
                'error'
            );
            return false;
        }
    } catch (error) {
        Modal.alert(I18n.t('network_error'), I18n.t('connect_error'), 'error');
        return false;
    }
}

// ========================================
// 模态框控制逻辑
// ========================================

function openApiConfigModal() {
    document.getElementById('apiConfigModal').hidden = false;
    setTimeout(() => {
        document.getElementById('apiConfigModal').querySelector('.modal-content').style.transform = 'scale(1)';
        document.getElementById('apiConfigModal').querySelector('.modal-content').style.opacity = '1';
    }, 10);
}

function closeApiConfigModal() {
    document.getElementById('apiConfigModal').hidden = true;
}

function openSystemConfigModal() {
    document.getElementById('systemConfigModal').hidden = false;
}

function closeSystemConfigModal() {
    document.getElementById('systemConfigModal').hidden = true;
}

async function openPricingModal() {
    const modal = document.getElementById('pricingModal');
    const editor = document.getElementById('pricingEditor');
    editor.innerHTML = `<p class="loading-cell">${I18n.t('pricing_loading')}</p>`;
    modal.hidden = false;
    try {
        const response = await apiFetch('/api/admin/model-pricing');
        if (!response.ok) throw new Error(I18n.t('pricing_load_failed'));
        const data = await response.json();
        editor.innerHTML = data.models.map(model => `
            <section class="pricing-model">
                <h4>${escapeHtml(model.name)}</h4>
                <div class="pricing-size-grid">
                    ${model.sizes.map(size => `
                        <label class="pricing-field">
                            <span>${escapeHtml(size.id)}</span>
                            <input type="number" min="0" max="100000" step="1"
                                value="${size.credits}" data-model-id="${model.id}" data-image-size="${size.id}">
                            <small>${I18n.t('pricing_credits_unit')}</small>
                        </label>`).join('')}
                </div>
            </section>`).join('');
    } catch (error) {
        editor.innerHTML = `<p class="error-message">${I18n.t('pricing_load_failed')}</p>`;
    }
}

// 显式挂到 window，保证生产环境 CSP/脚本加载方式下 HTML 的 onclick 始终能调用。
window.openPricingModal = openPricingModal;
window.closePricingModal = closePricingModal;
window.saveModelPricing = saveModelPricing;

function closePricingModal() {
    document.getElementById('pricingModal').hidden = true;
}

async function saveModelPricing() {
    const inputs = document.querySelectorAll('#pricingEditor input[data-model-id]');
    const prices = Array.from(inputs).map(input => ({
        model_id: input.dataset.modelId,
        image_size: input.dataset.imageSize,
        credits: input.value
    }));
    if (!prices.length || prices.some(price => !/^\d+$/.test(price.credits))) {
        Modal.toast(I18n.t('pricing_input_invalid'), 'warning');
        return;
    }
    try {
        const response = await apiFetch('/api/admin/model-pricing', {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prices })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(I18n.translateError(data.error, 'save_failed'));
        Modal.toast(I18n.t('pricing_saved'), 'success');
        closePricingModal();
    } catch (error) {
        Modal.alert(I18n.t('save_failed'), I18n.translateError(error.message, 'save_failed'), 'error');
    }
}

function openEmailConfigModal() {
    document.getElementById('emailConfigModal').hidden = false;
}

function closeEmailConfigModal() {
    document.getElementById('emailConfigModal').hidden = true;
}

// 覆盖 saveApiSettings 成功后的操作，确保关闭所有的模态框
const originalSaveApiSettings = saveApiSettings;
saveApiSettings = async function () {
    const saved = await originalSaveApiSettings();
    if (saved) {
        closeApiConfigModal();
        closeSystemConfigModal();
        closeEmailConfigModal();
    }
};

// 初始化
initDatePicker();
loadUsers();
loadCardKeys();
loadApiSettings();

document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const closers = [
        ['adminImageModal', closeImagePreview],
        ['pricingModal', closePricingModal],
        ['emailConfigModal', closeEmailConfigModal],
        ['systemConfigModal', closeSystemConfigModal],
        ['apiConfigModal', closeApiConfigModal],
        ['sessionModal', closeSessionModal]
    ];
    const visibleModal = closers.find(([id]) => !document.getElementById(id)?.hidden);
    if (visibleModal) visibleModal[1]();
});
