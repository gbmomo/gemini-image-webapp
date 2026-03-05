// ========================================
// 管理后台逻辑（从 admin.html 提取）
// ========================================

let users = [];
let currentSessions = []; // Store current user sessions (list only)
let currentViewUserId = null; // Track which user's sessions are being viewed

// 加载用户数据
async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users');
        if (response.ok) {
            users = await response.json();
            renderUsers();
            updateStats();
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else if (response.status === 403) {
            await Modal.alert(I18n.t('permission_error'), I18n.t('no_admin_permission'), 'error');
            window.location.href = '/';
        }
    } catch (error) {
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
            <td>${user.id}</td>
            <td>
                <span class="username">${user.username}</span>
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
                <button class="btn-action btn-view" onclick="viewSessions(${user.id}, '${user.username}')">
                    ${I18n.t('view_sessions')}
                </button>
                ${user.username !== 'admin' ? `
                    <button class="btn-action btn-toggle" onclick="toggleAdmin(${user.id})">
                        ${user.is_admin ? I18n.t('revoke_admin') : I18n.t('set_admin')}
                    </button>
                    <button class="btn-action btn-view" onclick="addCredits(${user.id}, '${user.username}')">
                        ${I18n.t('add_credits')}
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteUser(${user.id}, '${user.username}')">
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

// 查看用户会话
async function viewSessions(userId, username) {
    document.getElementById('modalTitle').textContent = `${username} - ${I18n.t('session_detail')}`;
    document.getElementById('sessionModal').hidden = false;
    currentViewUserId = userId;

    // Reset UI
    const sidebarList = document.getElementById('sessionSidebarList');
    const mainContent = document.getElementById('sessionMainContent');
    sidebarList.innerHTML = `<div style="padding:10px; color:var(--text-muted)">${I18n.t('loading')}</div>`;
    mainContent.innerHTML = '';

    try {
        const response = await fetch(`/api/admin/users/${userId}/sessions`);
        currentSessions = await response.json();

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
        <div class="session-list-item" id="session-item-${session.id}" onclick="selectSession('${session.id}')">
            <div class="session-list-item-title">${title}</div>
            <div class="session-list-item-date">${formatDate(session.updated_at)} · ${session.message_count || 0} ${I18n.t('messages_count')}</div>
        </div>
    `}).join('');
}

async function selectSession(sessionId) {
    // Update active state in sidebar
    document.querySelectorAll('.session-list-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.getElementById(`session-item-${sessionId}`);
    if (activeItem) activeItem.classList.add('active');

    const mainContent = document.getElementById('sessionMainContent');

    // 从服务器加载单个会话的消息
    mainContent.innerHTML = `<div class="viewer-empty"><div class="viewer-empty-icon">⏳</div><p>${I18n.t('loading')}</p></div>`;

    try {
        const response = await fetch(`/api/admin/users/${currentViewUserId}/sessions/${sessionId}`);
        if (!response.ok) {
            mainContent.innerHTML = `<div class="viewer-empty"><div class="viewer-empty-icon">❌</div><p>${I18n.t('load_sessions_failed')}</p></div>`;
            return;
        }
        const session = await response.json();

        if (!session.messages || session.messages.length === 0) {
            mainContent.innerHTML = `
                <div class="viewer-empty">
                    <div class="viewer-empty-icon">💬</div>
                    <p>${I18n.t('no_messages')}</p>
                </div>
            `;
            return;
        }

        mainContent.innerHTML = session.messages.map(msg => `
            <div class="viewer-message ${msg.role}">
                <div class="viewer-avatar">${msg.role === 'user' ? '👤' : '🤖'}</div>
                <div class="viewer-content-wrapper">
                     <div class="viewer-bubble">
                        ${msg.content || ''}
                        ${msg.image ? `<img src="${msg.thumbnail || msg.image}" class="viewer-image" alt="${I18n.t('generated_image')}" onclick="openImagePreview('${msg.image}')">` : ''}
                    </div>
                     <!-- Reference Images -->
                     ${msg.reference_images ? `
                        <div style="margin-top: 5px; display: flex; gap: 5px; flex-wrap: wrap;">
                            ${msg.reference_images.map(ref => `
                                <img src="/static/images/${ref}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover; border: 1px solid rgba(255,255,255,0.1);">
                            `).join('')}
                        </div>
                     ` : ''}
                </div>
            </div>
        `).join('');

        // Scroll to bottom
        setTimeout(() => {
            mainContent.scrollTop = mainContent.scrollHeight;
        }, 0);

    } catch (error) {
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
}

// 切换管理员状态
async function toggleAdmin(userId) {
    try {
        const response = await fetch(`/api/admin/users/${userId}/toggle-admin`, {
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
async function deleteUser(userId, username) {
    const confirmed = await Modal.confirm(I18n.t('delete_user'), I18n.t('confirm_delete_user', username), 'warning');
    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
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
async function addCredits(userId, username) {
    const amountStr = await Modal.prompt(I18n.t('credits_recharge'), I18n.t('credits_recharge_prompt', username), '10');
    if (amountStr === null) return;

    const amount = parseInt(amountStr);
    if (isNaN(amount) || amount === 0) {
        Modal.toast(I18n.t('invalid_number'), 'warning');
        return;
    }

    try {
        const response = await fetch(`/api/admin/users/${userId}/credits`, {
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
    const cutoffDate = date.toISOString().split('T')[0];

    await performCleanup(cutoffDate);
}

async function cleanupAllData() {
    const confirmed = await Modal.confirm(
        I18n.t('cleanup_all_title') || '清理所有数据',
        I18n.t('cleanup_all_msg') || '确定要清理所有数据吗？此操作将删除全部会话、图片和缩略图，且不可恢复！',
        'warning'
    );
    if (!confirmed) {
        return;
    }

    // 用明天的日期作为截止日期，确保所有数据都被清理
    const date = new Date();
    date.setDate(date.getDate() + 1);
    const cutoffDate = date.toISOString().split('T')[0];

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
        const response = await fetch('/api/admin/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cutoff_date: cutoffDate })
        });

        const data = await response.json();

        if (response.ok) {
            const stats = data.deleted_stats;
            let message = `${I18n.t('cleanup_complete')}!\nMessages: ${stats.messages}\nImages: ${stats.images}\nSessions: ${stats.sessions}`;
            if (stats.orphan_images > 0 || stats.orphan_thumbnails > 0) {
                message += `\n\nOrphan files:\n- Images: ${stats.orphan_images}\n- Thumbnails: ${stats.orphan_thumbnails}`;
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
        const response = await fetch('/api/admin/card-keys');
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
            <td>${key.used_by_username || '-'}</td>
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
        const response = await fetch('/api/admin/card-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credits, count })
        });

        const data = await response.json();

        if (response.ok) {
            const keysHTML = data.keys.map(key => `
                <div style="margin-bottom: 8px; padding: 10px; background: rgba(139, 92, 246, 0.1); border-radius: 8px;">
                    <code style="font-size: 1rem; font-weight: 600; color: var(--accent-purple-light); letter-spacing: 1px;">${key.code}</code>
                    <button onclick="navigator.clipboard.writeText('${key.code}').then(() => Modal.toast('${I18n.t('copied')}', 'success'))" style="margin-left: 10px; padding: 4px 8px; background: rgba(99, 102, 241, 0.2); color: var(--accent-blue); border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">${I18n.t('copy')}</button>
                </div>
            `).join('');

            await Modal.alert(
                I18n.t('keys_generated'),
                `<div style="max-height: 400px; overflow-y: auto;">
                    <p style="color: #f59e0b; font-weight: 600; margin-bottom: 12px;">${I18n.t('save_keys_warning')}</p>
                    ${keysHTML}
                </div>`,
                'success'
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

// 监听语言切换
I18n.onLangChange(() => {
    initDatePicker();
    // 重新渲染用户表格和卡密表格以更新翻译
    renderUsers();
    renderCardKeys();
});

// 初始化
initDatePicker();
loadUsers();
loadCardKeys();
