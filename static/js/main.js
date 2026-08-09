/**
 * Gemini 图像生成器 - 前端逻辑
 */

// 状态管理
const state = {
    currentSessionId: null,
    sessions: [],
    referenceImages: [],  // 改为数组，支持多张
    selectedResolution: '1K',
    selectedAspectRatio: '1:1',
    selectedThinkingLevel: 'minimal',
    selectedModel: window.DEFAULT_MODEL || 'gemini-3.1-flash-image',  // 从后端环境变量读取默认模型
    models: [],
    modelConfigAvailable: false,
    isGenerating: false,
    isSettingsLocked: false,  // 会话生成后锁定设置
    isLoadingSession: false,  // 会话历史加载中
    pendingReferenceCount: 0,
    pendingReferenceBytes: 0,
    referenceUploadGeneration: 0
};

// 服务端暂时不可用时仍可渲染可选项；正常情况下价格和能力始终以 /api/models 为准。
const FALLBACK_MODELS = [
    { id: 'gemini-3.1-flash-lite-image', name: 'Nano Banana 2 Lite', sizes: [{ id: '1K', credits: 1 }], ratios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'], max_references: 14, thinking_levels: ['minimal', 'high'], default_thinking_level: 'minimal' },
    { id: 'gemini-3.1-flash-image', name: 'Nano Banana 2', sizes: [{ id: '512', credits: 1 }, { id: '1K', credits: 1 }, { id: '2K', credits: 2 }, { id: '4K', credits: 4 }], ratios: ['1:1', '1:4', '1:8', '2:3', '3:2', '3:4', '4:1', '4:3', '4:5', '5:4', '8:1', '9:16', '16:9', '21:9'], max_references: 14, thinking_levels: ['minimal', 'high'], default_thinking_level: 'minimal' },
    { id: 'gemini-3-pro-image', name: 'Nano Banana Pro', sizes: [{ id: '1K', credits: 1 }, { id: '2K', credits: 2 }, { id: '4K', credits: 4 }], ratios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'], max_references: 14, thinking_levels: [], default_thinking_level: null },
    { id: 'gemini-2.5-flash-image', name: 'Nano Banana', sizes: [{ id: '1K', credits: 1 }], ratios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'], max_references: 3, thinking_levels: [], default_thinking_level: null }
];

// 会话数据缓存（避免重复加载，LRU 策略限制最多 50 个）
const sessionCache = new Map();
const SESSION_CACHE_MAX = 50;
const MAX_REFERENCE_FILE_BYTES = 10 * 1024 * 1024;
const MAX_REFERENCE_TOTAL_BYTES = 35 * 1024 * 1024;
const GUEST_DRAFT_KEY = 'nano_banana_guest_draft';
let imageModalReturnFocus = null;

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

window.apiFetch = apiFetch;

function saveGuestDraft() {
    if (window.IS_AUTHENTICATED) return;
    try {
        sessionStorage.setItem(GUEST_DRAFT_KEY, JSON.stringify({
            prompt: elements.promptInput?.value || '',
            model: state.selectedModel,
            thinking_level: state.selectedThinkingLevel,
            image_size: state.selectedResolution,
            aspect_ratio: state.selectedAspectRatio
        }));
    } catch (error) {
        console.warn('Unable to save the guest draft:', error);
    }
}

window.saveGuestDraft = saveGuestDraft;

function showAuthentication(mode = 'login', saveDraft = true) {
    if (saveDraft) saveGuestDraft();
    if (typeof window.openAuthModal === 'function') {
        window.openAuthModal(mode);
        return;
    }
    const authOverlay = document.getElementById('authModalOverlay');
    if (authOverlay) {
        authOverlay.classList.add('auth-modal-show');
        authOverlay.setAttribute('aria-hidden', 'false');
    } else {
        window.setTimeout(() => window.location.reload(), 0);
    }
}

function requireAuthentication(mode = 'login') {
    if (window.IS_AUTHENTICATED) return true;
    showAuthentication(mode);
    return false;
}

function handleUnauthorized() {
    window.IS_AUTHENTICATED = false;
    showAuthentication('login');
}

function restoreGuestDraft() {
    if (!window.IS_AUTHENTICATED) return false;
    let draft;
    try {
        const storedDraft = sessionStorage.getItem(GUEST_DRAFT_KEY);
        if (!storedDraft) return false;
        sessionStorage.removeItem(GUEST_DRAFT_KEY);
        draft = JSON.parse(storedDraft);
    } catch (error) {
        try {
            sessionStorage.removeItem(GUEST_DRAFT_KEY);
        } catch (_) {
            // Storage may be unavailable; there is nothing else to restore.
        }
        console.warn('Unable to restore the guest draft:', error);
        return false;
    }

    if (!draft || typeof draft !== 'object' || Array.isArray(draft)) return false;
    const model = state.models.find(item => item.id === draft.model) || currentModel();
    if (!model) return false;

    state.selectedModel = model.id;
    if (model.sizes.some(size => size.id === draft.image_size)) {
        state.selectedResolution = draft.image_size;
    }
    if (model.ratios.includes(draft.aspect_ratio)) {
        state.selectedAspectRatio = draft.aspect_ratio;
    }
    if (model.thinking_levels?.includes(draft.thinking_level)) {
        state.selectedThinkingLevel = draft.thinking_level;
    } else {
        state.selectedThinkingLevel = model.default_thinking_level;
    }
    if (typeof draft.prompt === 'string') {
        elements.promptInput.value = draft.prompt;
    }
    renderModelOptions();
    refreshCapabilityOptions();
    showEmptyState();
    return true;
}

async function requestJson(url, options = {}, fallbackKey = 'request_failed') {
    const response = await apiFetch(url, options);
    const contentType = response.headers.get('content-type') || '';
    let data = null;

    if (contentType.includes('application/json')) {
        data = await response.json();
    } else {
        const body = await response.text();
        if (body && response.ok) {
            throw new Error(I18n.t('invalid_server_response'));
        }
    }

    if (!response.ok) {
        if (response.status === 401) {
            handleUnauthorized();
        }
        const message = data?.error;
        const translated = message
            ? I18n.translateError(message, fallbackKey)
            : `${I18n.t(fallbackKey)} (HTTP ${response.status})`;
        const error = new Error(translated);
        error.status = response.status;
        throw error;
    }

    return data;
}

function sessionCacheSet(key, value) {
    if (sessionCache.size >= SESSION_CACHE_MAX) {
        // 删除最早的缓存项（Map 保持插入顺序）
        const firstKey = sessionCache.keys().next().value;
        sessionCache.delete(firstKey);
    }
    sessionCache.set(key, value);
}

// DOM 元素
const elements = {
    // 侧边栏
    btnNewChat: document.getElementById('btnNewChat'),
    sessionList: document.getElementById('sessionList'),
    sidebar: document.getElementById('sidebar'),
    sidebarOverlay: document.getElementById('sidebarOverlay'),
    hamburgerBtn: document.getElementById('hamburgerBtn'),
    sidebarCloseBtn: document.getElementById('sidebarCloseBtn'),

    // 控制面板
    uploadArea: document.getElementById('uploadArea'),
    referenceImage: document.getElementById('referenceImage'),
    previewList: document.getElementById('previewList'),
    promptInput: document.getElementById('promptInput'),
    resolutionGroup: document.getElementById('resolutionGroup'),
    resolutionSelect: document.getElementById('resolutionSelect'),
    aspectRatioSelect: document.getElementById('aspectRatioSelect'),
    thinkingLevelSelect: document.getElementById('thinkingLevelSelect'),
    modelSelect: document.getElementById('modelSelect'),
    modelConfigStatus: document.getElementById('modelConfigStatus'),
    btnGenerate: document.getElementById('btnGenerate'),

    // 预览区域
    previewContent: document.getElementById('previewContent'),
    emptyState: document.getElementById('emptyState'),
    messageList: document.getElementById('messageList'),

    // 加载和模态框
    loadingOverlay: document.getElementById('loadingOverlay'),
    sessionLoadingBar: document.getElementById('sessionLoadingBar'),
    imageModal: document.getElementById('imageModal'),
    modalBackdrop: document.getElementById('modalBackdrop'),
    modalImage: document.getElementById('modalImage'),
    btnDownload: document.getElementById('btnDownload'),
    btnCloseModal: document.getElementById('btnCloseModal')
};

// ========================================
// API 请求
// ========================================

async function fetchSessions() {
    const data = await requestJson('/api/sessions', {}, 'load_sessions_failed');
    if (!Array.isArray(data)) throw new Error(I18n.t('sessions_format_invalid'));
    return data;
}

async function createSession() {
    return requestJson('/api/sessions', { method: 'POST' }, 'create_session_failed');
}

async function getSession(sessionId) {
    return requestJson(`/api/sessions/${encodeURIComponent(sessionId)}`, {}, 'session_detail_failed');
}

async function deleteSession(sessionId) {
    await requestJson(`/api/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' }, 'delete_session_failed');
    return true;
}

async function generateImage(sessionId, prompt, aspectRatio, imageSize, referenceImages, model, thinkingLevel) {
    try {
        const response = await apiFetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                prompt,
                aspect_ratio: aspectRatio,
                image_size: imageSize,
                reference_images: referenceImages,  // 改为数组
                model: model,
                ...(thinkingLevel ? { thinking_level: thinkingLevel } : {})
            })
        });

        // 尝试解析 JSON，处理服务器返回 HTML 的情况
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            // 服务器返回了非 JSON（如 HTML 错误页面）
            const text = await response.text();
            console.error('Server returned non-JSON:', text.substring(0, 200));
            throw new Error(I18n.t('error_server_error'));
        }

        if (!response.ok) {
            if (response.status === 401) {
                handleUnauthorized();
            }
            // 如果错误消息是错误代码（以 error_ 开头），则翻译它
            const translatedError = I18n.translateError(data.error, 'generate_failed');
            throw new Error(translatedError);
        }

        return data;
    } catch (error) {
        console.error('Image generation failed:', error);
        throw error;
    }
}

async function loadModelCapabilities() {
    let data;
    try {
        const response = await apiFetch('/api/models');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        data = await response.json();
        if (!Array.isArray(data.models) || data.models.length === 0) throw new Error(I18n.t('model_config_empty'));
        state.modelConfigAvailable = true;
    } catch (error) {
        console.error('加载服务端模型配置失败，已使用内置选项：', error);
        data = { models: FALLBACK_MODELS, default: 'gemini-3.1-flash-image' };
        state.modelConfigAvailable = false;
    }
    state.models = data.models;
    state.selectedModel = state.models.some(model => model.id === state.selectedModel)
        ? state.selectedModel : data.default;
    renderModelOptions();
    refreshCapabilityOptions();
    elements.btnGenerate.disabled = !state.modelConfigAvailable;
    elements.btnGenerate.title = state.modelConfigAvailable ? '' : I18n.t('realtime_model_config_unavailable');
    updateModelConfigStatus();
}

function updateModelConfigStatus() {
    if (!elements.modelConfigStatus) return;
    elements.modelConfigStatus.hidden = state.modelConfigAvailable;
    elements.modelConfigStatus.textContent = state.modelConfigAvailable
        ? '' : `${I18n.t('error_service_unavailable')} (/api/models)`;
}

function currentModel() {
    return state.models.find(model => model.id === state.selectedModel);
}

function fillSelect(select, options, selected, label) {
    select.innerHTML = options.map(option => `<option value="${escapeHtml(option.id)}">${escapeHtml(option.label)}</option>`).join('');
    select.value = options.some(option => option.id === selected) ? selected : options[0]?.id;
    return select.value;
}

function renderModelOptions() {
    state.selectedModel = fillSelect(elements.modelSelect,
        state.models.map(model => ({ id: model.id, label: model.name })), state.selectedModel);
}

function refreshCapabilityOptions() {
    const model = currentModel();
    if (!model) return;
    state.selectedResolution = fillSelect(elements.resolutionSelect,
        model.sizes.map(size => ({ id: size.id, label: `${size.id} · 🪙 ${size.credits} ${I18n.t('credit_unit')}` })), state.selectedResolution);
    state.selectedAspectRatio = fillSelect(elements.aspectRatioSelect,
        model.ratios.map(ratio => ({ id: ratio, label: ratio })), state.selectedAspectRatio);
    const thinkingLevels = Array.isArray(model.thinking_levels) ? model.thinking_levels : [];
    if (thinkingLevels.length > 0) {
        state.selectedThinkingLevel = fillSelect(
            elements.thinkingLevelSelect,
            thinkingLevels.map(level => ({
                id: level,
                label: I18n.t(level === 'high' ? 'thinking_high' : 'thinking_minimal')
            })),
            state.selectedThinkingLevel || model.default_thinking_level || 'minimal'
        );
        elements.thinkingLevelSelect.disabled = state.isSettingsLocked;
    } else {
        fillSelect(elements.thinkingLevelSelect, [
            { id: 'automatic', label: I18n.t('thinking_automatic') }
        ], 'automatic');
        elements.thinkingLevelSelect.disabled = true;
    }
    const hint = document.querySelector('[data-i18n="max_images_hint"]');
    if (hint) hint.textContent = I18n.t('max_images_count', model.max_references);
}

// ========================================
// UI 更新
// ========================================

function renderSessionList() {
    elements.sessionList.innerHTML = state.sessions.map(session => {
        // 将后端默认的 '新对话' 翻译为当前语言
        const title = session.title === '新对话' ? I18n.t('new_chat') : session.title;
        return `
        <div class="session-item ${session.id === state.currentSessionId ? 'active' : ''}" 
             data-id="${session.id}">
            <div class="session-title">${escapeHtml(title)}</div>
            <div class="session-meta">${session.message_count} ${I18n.t('messages_count')}</div>
            <button class="session-delete" data-id="${session.id}" title="${I18n.t('delete')}">🗑️</button>
        </div>
    `}).join('');

    // 绑定点击事件
    elements.sessionList.querySelectorAll('.session-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('session-delete')) {
                selectSession(item.dataset.id);
            }
        });
    });

    // 绑定删除事件
    elements.sessionList.querySelectorAll('.session-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const sessionId = btn.dataset.id;
            const confirmed = await Modal.confirm(
                I18n.t('delete'),
                I18n.t('confirm_delete_session'),
                'warning'
            );
            if (!confirmed) return;
            try {
                await deleteSession(sessionId);
                sessionCache.delete(sessionId);
                state.sessions = state.sessions.filter(s => s.id !== sessionId);
                if (state.currentSessionId === sessionId) {
                    state.currentSessionId = null;
                    showEmptyState();
                }
                renderSessionList();
            } catch (error) {
                console.error('删除会话失败:', error);
                Modal.alert(I18n.t('delete'), error.message, 'error');
            }
        });
    });
}

function renderMessages(messages) {
    if (!messages || messages.length === 0) {
        showEmptyState();
        return;
    }

    elements.emptyState.hidden = true;
    elements.messageList.hidden = false;

    elements.messageList.innerHTML = messages.map(msg => {
        const isUser = msg.role === 'user';
        const avatar = isUser ? '👤' : '🤖';
        const roleClass = isUser ? 'user' : 'assistant';

        let contentHtml = '';

        // Chat Bubble Content
        if (msg.content) {
            contentHtml += `<div class="chat-text">${escapeHtml(msg.content)}</div>`;
        }

        // Generated Image (Assistant only usually)
        // Use thumbnail for preview if available, original for modal view
        if (msg.image) {
            const previewSrc = escapeHtml(msg.thumbnail || msg.image);
            const originalSrc = escapeHtml(msg.image);
            contentHtml += `<img class="chat-image" src="${previewSrc}" alt="${I18n.t('generated_image')}" data-src="${originalSrc}" loading="lazy">`;
            contentHtml += `<div class="chat-image-hint">${I18n.t('click_to_view')}</div>`;
        }

        // Reference Images (User only usually)
        let refImagesHtml = '';
        if (msg.reference_images && msg.reference_images.length > 0) {
            refImagesHtml += '<div class="chat-ref-images">';
            for (const refImg of msg.reference_images) {
                refImagesHtml += `<img class="chat-ref-image" src="/static/images/${escapeHtml(refImg)}" alt="${I18n.t('reference_image')}" loading="lazy">`;
            }
            refImagesHtml += '</div>';
        }
        // Compatibility for old single image
        if (msg.reference_image) {
            refImagesHtml += `<div class="chat-ref-images"><img class="chat-ref-image" src="/static/images/${escapeHtml(msg.reference_image)}" alt="${I18n.t('reference_image')}" loading="lazy"></div>`;
        }

        return `
        <div class="chat-message ${roleClass}">
            <div class="chat-avatar">${avatar}</div>
            <div class="chat-content-wrapper">
                ${refImagesHtml}
                ${contentHtml ? `<div class="chat-bubble">${contentHtml}</div>` : ''}
            </div>
        </div>
        `;
    }).join('');

    // Bind image click events
    elements.messageList.querySelectorAll('.chat-image').forEach(img => {
        img.addEventListener('click', () => openImageModal(img.dataset.src));
    });

    // Scroll to bottom
    setTimeout(() => {
        elements.previewContent.scrollTop = elements.previewContent.scrollHeight;
    }, 0);
}

function showEmptyState() {
    elements.emptyState.hidden = false;
    elements.messageList.hidden = true;
    elements.messageList.innerHTML = '';
}

function showLoading(show) {
    elements.loadingOverlay.hidden = !show;
    state.isGenerating = show;
    elements.btnGenerate.disabled = show || !state.modelConfigAvailable;
}

function openImageModal(src) {
    imageModalReturnFocus = document.activeElement;
    elements.modalImage.src = src;
    elements.btnDownload.href = src;
    elements.imageModal.hidden = false;
    elements.btnCloseModal.focus();
}

function closeImageModal() {
    elements.imageModal.hidden = true;
    if (imageModalReturnFocus instanceof HTMLElement) imageModalReturnFocus.focus();
    imageModalReturnFocus = null;
}

function showSessionLoadingBar() {
    state.isLoadingSession = true;

    if (elements.sessionLoadingBar) {
        elements.sessionLoadingBar.hidden = false;
        // 使用 setTimeout 确保元素先显示，然后触发动画
        setTimeout(() => {
            elements.sessionLoadingBar.classList.add('loading');
        }, 10);
    }

    // 禁用控制面板，防止加载期间误操作
    const controlPanel = document.querySelector('.control-panel');
    if (controlPanel) {
        controlPanel.classList.add('panel-disabled');
    }
}

function hideSessionLoadingBar() {
    state.isLoadingSession = false;

    if (elements.sessionLoadingBar) {
        elements.sessionLoadingBar.classList.remove('loading');
        elements.sessionLoadingBar.classList.add('complete');
        // 等待动画结束后隐藏
        setTimeout(() => {
            elements.sessionLoadingBar.hidden = true;
            elements.sessionLoadingBar.classList.remove('complete');
        }, 500);
    }

    // 恢复控制面板
    const controlPanel = document.querySelector('.control-panel');
    if (controlPanel) {
        controlPanel.classList.remove('panel-disabled');
    }
}

// ========================================
// 会话管理
// ========================================

async function loadSessions() {
    try {
        state.sessions = await fetchSessions();
        renderSessionList();
    } catch (error) {
        console.error('获取会话列表失败:', error);
        state.sessions = [];
        renderSessionList();
        if (error.status !== 401) Modal.toast(error.message, 'error');
    }
}

async function selectSession(sessionId) {
    if (state.isLoadingSession) return;

    state.currentSessionId = sessionId;
    renderSessionList();

    // 检查缓存
    const cached = sessionCache.get(sessionId);
    if (cached) {
        // 缓存命中，直接渲染，无需加载条
        renderMessages(cached.messages);
        if (cached.settings) {
            applyLockedSettings(cached.settings);
            lockSettings();
        } else {
            unlockSettings();
        }
    } else {
        // 缓存未命中，从服务器加载
        showSessionLoadingBar();

        try {
            const session = await getSession(sessionId);
            if (state.currentSessionId !== sessionId) return;
            sessionCacheSet(sessionId, session);
            renderMessages(session.messages);

            if (session.settings) {
                applyLockedSettings(session.settings);
                lockSettings();
            } else {
                unlockSettings();
            }
        } catch (error) {
            console.error('获取会话详情失败:', error);
            if (error.status !== 401) Modal.toast(error.message, 'error');
        } finally {
            hideSessionLoadingBar();
        }
    }

    // 移动端选择后关闭侧边栏
    if (window.innerWidth <= 768) {
        closeSidebar();
    }
}

async function handleNewChat() {
    if (state.isGenerating || state.isLoadingSession) return null;
    if (!requireAuthentication()) return null;
    try {
        const session = await createSession();
        state.sessions.unshift(session);
        state.currentSessionId = session.id;
        renderSessionList();
        showEmptyState();
        elements.promptInput.value = '';
        clearReferenceImages();
        unlockSettings();  // 新会话解锁设置
        resetSettingsToDefault();  // 重置为默认值
        elements.promptInput.focus();

        // 移动端新建后关闭侧边栏
        if (window.innerWidth <= 768) {
            closeSidebar();
        }
        return session;
    } catch (error) {
        console.error('创建会话失败:', error);
        if (error.status !== 401) Modal.alert(I18n.t('new_chat'), error.message, 'error');
        return null;
    }
}

// ========================================
// 图片上传
// ========================================

function dataUrlByteLength(dataUrl) {
    const base64 = dataUrl.split(',', 2)[1] || '';
    return Math.max(0, Math.floor(base64.length * 3 / 4) - (base64.endsWith('==') ? 2 : base64.endsWith('=') ? 1 : 0));
}

function readImageFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error(I18n.t('read_image_failed', file.name)));
        reader.readAsDataURL(file);
    });
}

async function handleImageUpload(files) {
    if (state.isLoadingSession) return;
    if (!requireAuthentication()) return;
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    const maxImages = currentModel()?.max_references || 14;
    const availableSlots = Math.max(0, maxImages - state.referenceImages.length - state.pendingReferenceCount);
    const existingBytes = state.referenceImages.reduce((total, image) => total + dataUrlByteLength(image), 0)
        + state.pendingReferenceBytes;
    const accepted = [];
    let selectedBytes = existingBytes;
    let invalidType = false;
    let tooLarge = false;
    let totalExceeded = false;

    let countExceeded = availableSlots === 0 && fileArray.length > 0;
    for (const file of fileArray) {
        if (!file || !file.type.startsWith('image/')) {
            invalidType = true;
            continue;
        }
        if (file.size > MAX_REFERENCE_FILE_BYTES) {
            tooLarge = true;
            continue;
        }
        if (selectedBytes + file.size > MAX_REFERENCE_TOTAL_BYTES) {
            totalExceeded = true;
            continue;
        }
        if (accepted.length >= availableSlots) {
            countExceeded = true;
            continue;
        }
        selectedBytes += file.size;
        accepted.push(file);
    }

    if (countExceeded) {
        Modal.toast(I18n.t('upload_count_exceeded', maxImages), 'warning');
    } else if (invalidType) {
        Modal.toast(I18n.t('upload_images_only'), 'warning');
    } else if (tooLarge) {
        Modal.toast(I18n.t('upload_single_too_large'), 'warning');
    } else if (totalExceeded) {
        Modal.toast(I18n.t('upload_total_too_large'), 'warning');
    }

    if (accepted.length === 0) return;

    const uploadGeneration = state.referenceUploadGeneration;
    const queuedBytes = accepted.reduce((total, file) => total + file.size, 0);
    state.pendingReferenceCount += accepted.length;
    state.pendingReferenceBytes += queuedBytes;
    try {
        const images = await Promise.all(accepted.map(readImageFile));
        if (uploadGeneration === state.referenceUploadGeneration) {
            state.referenceImages.push(...images);
            renderPreviewList();
        }
    } catch (error) {
        Modal.toast(error.message, 'error');
    } finally {
        state.pendingReferenceCount = Math.max(0, state.pendingReferenceCount - accepted.length);
        state.pendingReferenceBytes = Math.max(0, state.pendingReferenceBytes - queuedBytes);
    }
}

function removeImage(index) {
    state.referenceImages.splice(index, 1);
    renderPreviewList();
}

function renderPreviewList() {
    elements.previewList.innerHTML = state.referenceImages.map((img, index) => `
        <div class="preview-item">
            <img src="${img}" alt="${I18n.t('reference_image')} ${index + 1}">
            <button class="btn-remove" data-index="${index}" aria-label="${I18n.t('remove_image')}">
                ✕
            </button>
        </div>
    `).join('');

    // 绑定删除按钮事件
    elements.previewList.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeImage(parseInt(btn.dataset.index));
        });
    });
}

function clearReferenceImages() {
    state.referenceUploadGeneration++;
    state.referenceImages = [];
    elements.referenceImage.value = '';
    renderPreviewList();
}

// ========================================
// 生成图像
// ========================================

async function handleGenerate() {
    if (state.isGenerating || state.isLoadingSession) return;
    if (!requireAuthentication()) return;

    if (!state.modelConfigAvailable) {
        Modal.alert(I18n.t('generate_failed'), I18n.t('realtime_model_config_unavailable'), 'error');
        return;
    }

    const prompt = elements.promptInput.value.trim();
    const model = currentModel();

    if (!prompt) {
        Modal.alert(I18n.t('enter_prompt'), I18n.t('enter_prompt'), 'warning');
        elements.promptInput.focus();
        return;
    }

    if (!model) {
        Modal.alert(I18n.t('generate_failed'), I18n.t('current_model_unavailable'), 'error');
        return;
    }

    if (state.referenceImages.length > model.max_references) {
        Modal.alert(
            I18n.t('reference_limit_title', model.max_references),
            I18n.t('reference_limit_message', model.name, model.max_references),
            'warning'
        );
        return;
    }

    // 如果没有当前会话，先创建一个（但保留当前选择的设置）
    if (!state.currentSessionId) {
        // 保存用户当前选择的设置
        const currentResolution = state.selectedResolution;
        const currentAspectRatio = state.selectedAspectRatio;
        const currentThinkingLevel = state.selectedThinkingLevel;
        const currentModel = state.selectedModel;

        const createdSession = await handleNewChat();
        if (!createdSession) return;

        // 恢复用户的设置（handleNewChat会重置为默认值）
        state.selectedResolution = currentResolution;
        state.selectedAspectRatio = currentAspectRatio;
        state.selectedThinkingLevel = currentThinkingLevel;
        state.selectedModel = currentModel;

        renderModelOptions();
        refreshCapabilityOptions();
    }

    showLoading(true);

    try {
        const result = await generateImage(
            state.currentSessionId,
            prompt,
            state.selectedAspectRatio,
            state.selectedResolution,
            state.referenceImages,  // 改为数组
            state.selectedModel,
            currentModel()?.thinking_levels?.includes(state.selectedThinkingLevel)
                ? state.selectedThinkingLevel
                : null
        );

        // 更新会话标题
        const session = state.sessions.find(s => s.id === state.currentSessionId);
        if (session && result.session_title) {
            session.title = result.session_title;
            session.message_count = (session.message_count || 0) + 2;
            renderSessionList();
        }

        // 更新点数显示
        if (result.credits_remaining !== undefined && result.credits_remaining !== 'admin') {
            const creditEl = document.getElementById('userCredits');
            if (creditEl) {
                creditEl.innerHTML = `🪙 ${result.credits_remaining} <span data-i18n="credits_label">${I18n.t('credits_label')}</span>`;
            }
        }

        // 直接用返回的数据更新缓存和界面（避免额外请求）
        let cached = sessionCache.get(state.currentSessionId);
        if (!cached) {
            cached = { messages: [], settings: null };
            sessionCacheSet(state.currentSessionId, cached);
        }

        // 追加用户消息
        cached.messages.push({
            role: 'user',
            content: prompt,
            reference_images: Array.isArray(result.reference_images) && result.reference_images.length > 0
                ? result.reference_images : null
        });

        // 追加 AI 响应
        cached.messages.push({
            role: 'assistant',
            content: result.text,
            image: result.image,
            thumbnail: result.thumbnail
        });

        // 更新设置锁定
        if (result.settings) {
            cached.settings = result.settings;
            applyLockedSettings(result.settings);
            lockSettings();
        }

        renderMessages(cached.messages);

        // 清除输入和参考图
        elements.promptInput.value = '';
        clearReferenceImages();

    } catch (error) {
        Modal.alert(I18n.t('generate_failed'), error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ========================================
// 选项按钮
// ========================================

// ========================================
// 设置锁定功能
// ========================================

function setSettingsLocked(locked) {
    state.isSettingsLocked = locked;
    const method = locked ? 'add' : 'remove';

    [elements.resolutionSelect, elements.aspectRatioSelect, elements.modelSelect, elements.thinkingLevelSelect].forEach(select => {
        select.disabled = locked;
        select.classList[method]('settings-locked');
    });
    if (!currentModel()?.thinking_levels?.length) {
        elements.thinkingLevelSelect.disabled = true;
    }
}

function lockSettings() {
    setSettingsLocked(true);
}

function unlockSettings() {
    setSettingsLocked(false);
}

function applyLockedSettings(settings) {
    // 应用锁定的分辨率
    if (settings.image_size) {
        state.selectedResolution = settings.image_size;
    }

    // 应用锁定的纵横比
    if (settings.aspect_ratio) {
        state.selectedAspectRatio = settings.aspect_ratio;
    }

    // 应用锁定的模型
    if (settings.model) {
        state.selectedModel = settings.model;
    }
    state.selectedThinkingLevel = settings.thinking_level ?? null;
    renderModelOptions();
    refreshCapabilityOptions();
}

function resetSettingsToDefault() {
    // 重置分辨率为 1K
    state.selectedResolution = '1K';

    // 重置纵横比为默认的 1:1
    state.selectedAspectRatio = '1:1';
    state.selectedThinkingLevel = 'minimal';

    // 重置模型为默认值
    const defaultModel = window.DEFAULT_MODEL || 'gemini-3.1-flash-image';
    state.selectedModel = defaultModel;
    renderModelOptions();
    refreshCapabilityOptions();
}

async function showSettingsLockedModal() {
    const confirmed = await Modal.confirm(
        I18n.t('settings_locked'),
        I18n.t('settings_locked_msg'),
        'warning'
    );

    if (confirmed) {
        // User clicked OK, create new chat
        await handleNewChat();
    }
}

// ========================================
// 工具函数
// ========================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// 事件绑定
// ========================================

function bindEvents() {
    // 新建对话
    elements.btnNewChat.addEventListener('click', handleNewChat);

    // 生成按钮
    elements.btnGenerate.addEventListener('click', handleGenerate);

    // 回车生成（Ctrl+Enter）
    elements.promptInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter' && !state.isLoadingSession && !state.isGenerating) {
            e.preventDefault();
            handleGenerate();
        }
    });

    // 图片上传
    elements.uploadArea.addEventListener('click', () => {
        if (!requireAuthentication()) return;
        elements.referenceImage.click();
    });

    elements.uploadArea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (!requireAuthentication()) return;
            elements.referenceImage.click();
        }
    });

    elements.referenceImage.addEventListener('change', (e) => {
        handleImageUpload(e.target.files);  // 传入整个files对象
        e.target.value = '';
    });

    // 拖拽上传
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('drag-over');
    });

    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.classList.remove('drag-over');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('drag-over');
        if (!requireAuthentication()) return;
        handleImageUpload(e.dataTransfer.files);  // 传入整个files对象
    });

    // 粘贴图片
    document.addEventListener('paste', (e) => {
        const items = e.clipboardData?.items;
        if (items) {
            const files = [];
            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    files.push(item.getAsFile());
                }
            }
            if (files.length > 0) {
                if (!requireAuthentication()) return;
                handleImageUpload(files);
            }
        }
    });

    // 下拉选择；锁定的会话切换到新对话后再继续选择。
    elements.modelSelect.addEventListener('change', () => {
        if (state.isSettingsLocked) return showSettingsLockedModal();
        state.selectedModel = elements.modelSelect.value;
        refreshCapabilityOptions();
    });
    elements.resolutionSelect.addEventListener('change', () => {
        if (state.isSettingsLocked) return showSettingsLockedModal();
        state.selectedResolution = elements.resolutionSelect.value;
    });
    elements.aspectRatioSelect.addEventListener('change', () => {
        if (state.isSettingsLocked) return showSettingsLockedModal();
        state.selectedAspectRatio = elements.aspectRatioSelect.value;
    });
    elements.thinkingLevelSelect.addEventListener('change', () => {
        if (state.isSettingsLocked) return showSettingsLockedModal();
        state.selectedThinkingLevel = elements.thinkingLevelSelect.value;
    });

    // 模态框
    elements.modalBackdrop.addEventListener('click', closeImageModal);
    elements.btnCloseModal.addEventListener('click', closeImageModal);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !elements.imageModal.hidden) {
            closeImageModal();
        }
    });

    // 移动端侧边栏
    if (elements.hamburgerBtn) {
        elements.hamburgerBtn.addEventListener('click', openSidebar);
    }
    if (elements.sidebarCloseBtn) {
        elements.sidebarCloseBtn.addEventListener('click', closeSidebar);
    }
    if (elements.sidebarOverlay) {
        elements.sidebarOverlay.addEventListener('click', closeSidebar);
    }
}

// ========================================
// 移动端侧边栏控制
// ========================================

function openSidebar() {
    if (elements.sidebar) {
        elements.sidebar.classList.add('open');
    }
    if (elements.sidebarOverlay) {
        elements.sidebarOverlay.classList.add('active');
    }
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    if (elements.sidebar) {
        elements.sidebar.classList.remove('open');
    }
    if (elements.sidebarOverlay) {
        elements.sidebarOverlay.classList.remove('active');
    }
    document.body.style.overflow = '';
}

// ========================================
// 初始化
// ========================================

async function init() {
    await loadModelCapabilities();
    bindEvents();

    if (window.IS_AUTHENTICATED) {
        const restoredGuestDraft = restoreGuestDraft();
        await loadSessions();

        // 如果有会话，选择第一个
        if (!restoredGuestDraft && state.sessions.length > 0) {
            await selectSession(state.sessions[0].id);
        }
    }

    // 监听语言切换，重新渲染会话列表和消息
    I18n.onLangChange(() => {
        updateModelConfigStatus();
        refreshCapabilityOptions();
        if (state.modelConfigAvailable) elements.btnGenerate.title = '';
        else elements.btnGenerate.title = I18n.t('realtime_model_config_unavailable');
        renderSessionList();
        // 如果有当前会话，重新渲染消息以更新图片alt等文本
        if (state.currentSessionId) {
            const cached = sessionCache.get(state.currentSessionId);
            if (cached) {
                renderMessages(cached.messages);
            } else {
                const requestedSessionId = state.currentSessionId;
                getSession(requestedSessionId).then(session => {
                    if (session && state.currentSessionId === requestedSessionId) {
                        sessionCache.set(requestedSessionId, session);
                        renderMessages(session.messages);
                    }
                }).catch(error => {
                    if (error.status !== 401) console.error('刷新会话失败:', error);
                });
            }
        }
    });
}

// 启动应用
init();
