/**
 * Gemini 图像生成器 - 前端逻辑
 */

// 状态管理
const state = {
    currentSessionId: null,
    sessions: [],
    referenceImages: [],  // 改为数组，支持多张
    selectedResolution: '1K',
    selectedAspectRatio: 'auto',
    selectedModel: 'gemini-3-pro-image-preview',  // 固定使用Nano Banana Pro
    isGenerating: false,
    isSettingsLocked: false,  // 会话生成后锁定设置
    isLoadingSession: false   // 会话历史加载中
};

// 会话数据缓存（避免重复加载）
const sessionCache = new Map();

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
    resolutionButtons: document.getElementById('resolutionButtons'),
    aspectRatioButtons: document.getElementById('aspectRatioButtons'),
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
    try {
        const response = await fetch('/api/sessions');
        return await response.json();
    } catch (error) {
        console.error('获取会话列表失败:', error);
        return [];
    }
}

async function createSession() {
    try {
        const response = await fetch('/api/sessions', { method: 'POST' });
        return await response.json();
    } catch (error) {
        console.error('创建会话失败:', error);
        return null;
    }
}

async function getSession(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        return await response.json();
    } catch (error) {
        console.error('获取会话详情失败:', error);
        return null;
    }
}

async function deleteSession(sessionId) {
    try {
        await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
        return true;
    } catch (error) {
        console.error('删除会话失败:', error);
        return false;
    }
}

async function generateImage(sessionId, prompt, aspectRatio, imageSize, referenceImages) {
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                prompt,
                aspect_ratio: aspectRatio,
                image_size: imageSize,
                reference_images: referenceImages  // 改为数组
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
            // 如果错误消息是错误代码（以 error_ 开头），则翻译它
            const errorMsg = data.error || 'generate_failed';
            const translatedError = errorMsg.startsWith('error_') ? I18n.t(errorMsg) : errorMsg;
            throw new Error(translatedError);
        }

        return data;
    } catch (error) {
        console.error('Image generation failed:', error);
        throw error;
    }
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
            await deleteSession(sessionId);
            sessionCache.delete(sessionId);
            state.sessions = state.sessions.filter(s => s.id !== sessionId);
            if (state.currentSessionId === sessionId) {
                state.currentSessionId = null;
                showEmptyState();
            }
            renderSessionList();
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
            const previewSrc = msg.thumbnail || msg.image;
            contentHtml += `<img class="chat-image" src="${previewSrc}" alt="${I18n.t('generated_image')}" data-src="${msg.image}" loading="lazy">`;
            contentHtml += `<div class="chat-image-hint">${I18n.t('click_to_view')}</div>`;
        }

        // Reference Images (User only usually)
        let refImagesHtml = '';
        if (msg.reference_images && msg.reference_images.length > 0) {
            refImagesHtml += '<div class="chat-ref-images">';
            for (const refImg of msg.reference_images) {
                refImagesHtml += `<img class="chat-ref-image" src="/static/images/${refImg}" alt="${I18n.t('reference_image')}" loading="lazy">`;
            }
            refImagesHtml += '</div>';
        }
        // Compatibility for old single image
        if (msg.reference_image) {
            refImagesHtml += `<div class="chat-ref-images"><img class="chat-ref-image" src="/static/images/${msg.reference_image}" alt="${I18n.t('reference_image')}" loading="lazy"></div>`;
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
    elements.btnGenerate.disabled = show;
}

function openImageModal(src) {
    elements.modalImage.src = src;
    elements.btnDownload.href = src;
    elements.imageModal.hidden = false;
}

function closeImageModal() {
    elements.imageModal.hidden = true;
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
    state.sessions = await fetchSessions();
    renderSessionList();
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

        const session = await getSession(sessionId);

        hideSessionLoadingBar();

        if (session) {
            sessionCache.set(sessionId, session);
            renderMessages(session.messages);

            if (session.settings) {
                applyLockedSettings(session.settings);
                lockSettings();
            } else {
                unlockSettings();
            }
        }
    }

    // 移动端选择后关闭侧边栏
    if (window.innerWidth <= 768) {
        closeSidebar();
    }
}

async function handleNewChat() {
    const session = await createSession();
    if (session) {
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
    }
}

// ========================================
// 图片上传
// ========================================

const MAX_IMAGES = 14;

function handleImageUpload(files) {
    if (state.isLoadingSession) return;
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);

    for (const file of fileArray) {
        if (!file.type.startsWith('image/')) continue;
        if (state.referenceImages.length >= MAX_IMAGES) {
            Modal.alert(I18n.t('upload_limit', MAX_IMAGES), I18n.t('upload_limit', MAX_IMAGES), 'warning');
            break;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            state.referenceImages.push(e.target.result);
            renderPreviewList();
        };
        reader.readAsDataURL(file);
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
            <button class="btn-remove" data-index="${index}">✕</button>
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
    state.referenceImages = [];
    elements.referenceImage.value = '';
    renderPreviewList();
}

// ========================================
// 生成图像
// ========================================

async function handleGenerate() {
    if (state.isLoadingSession) return;

    const prompt = elements.promptInput.value.trim();

    if (!prompt) {
        Modal.alert(I18n.t('enter_prompt'), I18n.t('enter_prompt'), 'warning');
        elements.promptInput.focus();
        return;
    }

    // 如果没有当前会话，先创建一个（但保留当前选择的设置）
    if (!state.currentSessionId) {
        // 保存用户当前选择的设置
        const currentResolution = state.selectedResolution;
        const currentAspectRatio = state.selectedAspectRatio;

        await handleNewChat();

        // 恢复用户的设置（handleNewChat会重置为默认值）
        state.selectedResolution = currentResolution;
        state.selectedAspectRatio = currentAspectRatio;

        // 更新UI按钮状态
        elements.resolutionButtons.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.value === currentResolution);
        });
        elements.aspectRatioButtons.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.value === currentAspectRatio);
        });
    }

    showLoading(true);

    try {
        const result = await generateImage(
            state.currentSessionId,
            prompt,
            state.selectedAspectRatio,
            state.selectedResolution,
            state.referenceImages  // 改为数组
        );

        // 更新会话标题
        const session = state.sessions.find(s => s.id === state.currentSessionId);
        if (session && result.session_title) {
            session.title = result.session_title;
            session.message_count += 2;
            renderSessionList();
        }

        // 更新点数显示
        if (result.credits_remaining !== undefined && result.credits_remaining !== 'admin') {
            const creditEl = document.getElementById('userCredits');
            if (creditEl) {
                creditEl.textContent = `🪙 ${result.credits_remaining} 点`;
            }
        }

        // 重新加载消息
        const sessionData = await getSession(state.currentSessionId);
        if (sessionData) {
            sessionCache.set(state.currentSessionId, sessionData);
            renderMessages(sessionData.messages);

            // 检查并应用锁定状态
            if (sessionData.settings) {
                applyLockedSettings(sessionData.settings);
                lockSettings();
            }
        }

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

function setupOptionButtons(container, stateKey) {
    container.querySelectorAll('.option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // 如果设置已锁定，显示提示弹窗
            if (state.isSettingsLocked) {
                showSettingsLockedModal();
                return;
            }

            container.querySelectorAll('.option-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state[stateKey] = btn.dataset.value;
        });
    });
}

// ========================================
// 设置锁定功能
// ========================================

function lockSettings() {
    state.isSettingsLocked = true;

    // 添加锁定样式
    elements.resolutionButtons.classList.add('settings-locked');
    elements.aspectRatioButtons.classList.add('settings-locked');

    // 禁用所有按钮
    elements.resolutionButtons.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.add('locked');
    });
    elements.aspectRatioButtons.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.add('locked');
    });
}

function unlockSettings() {
    state.isSettingsLocked = false;

    // 移除锁定样式
    elements.resolutionButtons.classList.remove('settings-locked');
    elements.aspectRatioButtons.classList.remove('settings-locked');

    // 启用所有按钮
    elements.resolutionButtons.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('locked');
    });
    elements.aspectRatioButtons.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('locked');
    });
}

function applyLockedSettings(settings) {
    // 应用锁定的分辨率
    if (settings.image_size) {
        state.selectedResolution = settings.image_size;
        elements.resolutionButtons.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.value === settings.image_size);
        });
    }

    // 应用锁定的纵横比
    if (settings.aspect_ratio) {
        state.selectedAspectRatio = settings.aspect_ratio;
        elements.aspectRatioButtons.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.value === settings.aspect_ratio);
        });
    }
}

function resetSettingsToDefault() {
    // 重置分辨率为 1K
    state.selectedResolution = '1K';
    elements.resolutionButtons.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === '1K');
    });

    // 重置纵横比为 auto
    state.selectedAspectRatio = 'auto';
    elements.aspectRatioButtons.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === 'auto');
    });
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
        if (e.ctrlKey && e.key === 'Enter' && !state.isLoadingSession) {
            handleGenerate();
        }
    });

    // 图片上传
    elements.uploadArea.addEventListener('click', () => {
        elements.referenceImage.click();
    });

    elements.referenceImage.addEventListener('change', (e) => {
        handleImageUpload(e.target.files);  // 传入整个files对象
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
                handleImageUpload(files);
            }
        }
    });

    // 选项按钮
    setupOptionButtons(elements.resolutionButtons, 'selectedResolution');
    setupOptionButtons(elements.aspectRatioButtons, 'selectedAspectRatio');

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
    bindEvents();
    await loadSessions();

    // 如果有会话，选择第一个
    if (state.sessions.length > 0) {
        await selectSession(state.sessions[0].id);
    }

    // 监听语言切换，重新渲染会话列表和消息
    I18n.onLangChange(() => {
        renderSessionList();
        // 如果有当前会话，重新渲染消息以更新图片alt等文本
        if (state.currentSessionId) {
            const cached = sessionCache.get(state.currentSessionId);
            if (cached) {
                renderMessages(cached.messages);
            } else {
                getSession(state.currentSessionId).then(session => {
                    if (session) {
                        sessionCache.set(state.currentSessionId, session);
                        renderMessages(session.messages);
                    }
                });
            }
        }
    });
}

// 启动应用
init();
