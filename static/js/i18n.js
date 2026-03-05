/**
 * Internationalization (i18n) Module
 * 国际化模块 - 支持中英文切换
 */

// ========================================
// 配置项 - 可以在这里修改默认语言
// ========================================
const DEFAULT_LANG = 'zh';  // 默认语言: 'zh' (中文) 或 'en' (英文)

// ========================================
// 翻译文本
// ========================================
const translations = {
    zh: {
        // 页面标题
        page_title: '码言旗下Nano Banana AI图片生成器',

        // 顶部横幅
        site_title: '码言nano',
        site_subtitle: '在线使用Nano Banana',
        banner_brand: '码言旗下',
        banner_product: '🍌 Nano Banana',
        banner_desc: '4K AI图片生成器',
        banner_price: '$0.04起/张',
        banner_trial: '免费试用',

        // 用户菜单
        credits_label: '点',
        recharge_btn: '💳 充值',
        admin_panel: '管理后台',
        logout: '退出',

        // 侧边栏
        sidebar_brand: '码言旗下',
        new_chat: '新对话',
        messages_count: '条消息',
        close_menu: '关闭菜单',
        open_menu: '打开菜单',

        // 控制面板
        reference_images: '参考图（可选）',
        max_images_hint: '最多14张',
        upload: '上传',
        upload_hint: '点击或拖拽',
        upload_desc: '可选：上传参考图进行图生图。支持拖拽或粘贴截图，最多14张',
        prompt_label: '提示词',
        prompt_placeholder: '例如：一只可爱的小猫咪坐在花园里，油画风格，高清，细节丰富',
        aspect_resolution: '模型 & 纵横比 & 分辨率',
        resolution_label: '分辨率(不同分辨率消耗点数数目不同)',
        aspect_ratio_label: '纵横比',
        model_label: 'AI 模型',
        model_nano_banana_pro: 'Nano Banana Pro',
        model_nano_banana_pro_desc: '专业创作',
        model_nano_banana_2: 'Nano Banana 2',
        model_nano_banana_2_desc: '最新模型',
        aspect_auto: 'auto 自适应',
        aspect_square: '1:1 方形',
        aspect_16_9: '16:9 横版',
        aspect_9_16: '9:16 竖版',
        aspect_4_3: '4:3 横版',
        aspect_3_4: '3:4 竖版',
        aspect_21_9: '21:9 超宽',
        aspect_3_2: '3:2 横版',
        aspect_2_3: '2:3 竖版',
        settings_warning: '⚠️ 更改模型、分辨率或纵横比会重置对话记忆，AI 将无法记住之前生成的图片',
        generate_btn: '生成图片',

        // 预览区
        chat_area: '聊天区',
        empty_state_title: '对话内容与生成的图片将在这里显示',
        empty_state_hint: '在左侧输入提示词，点击生成按钮开始创作',
        click_to_view: '✨ 点击图片查看高清大图或下载',

        // 加载状态
        loading_text: '正在生成图片...',
        loading_hint: '预计耗时 1 min',

        // 图片预览模态框
        image_preview: '大图预览',
        download_image: '📥 下载图片',

        // 充值模态框
        recharge_title: '点数充值',
        buy_card: '购买卡密',
        buy_card_desc: '在商城购买点数卡密，获取充值码',
        go_buy: '去购买 →',
        or: '或',
        enter_card_key: '输入卡密充值',
        card_key_placeholder: '请输入16位卡密码',
        confirm_recharge: '确认充值',
        current_credits: '当前点数：',

        // 登录/注册
        welcome_back: '欢迎回来',
        login_subtitle: '登录码言 Nano Banana 创作',
        username: '用户名',
        username_placeholder: '请输入用户名',
        password: '密码',
        password_placeholder: '请输入密码',
        login_btn: '登 录',
        no_account: '还没有账号？',
        register_now: '立即注册',
        create_account: '创建账号',
        register_subtitle: '加入码言 Nano Banana 开启 AI 之旅',
        username_hint: '至少3个字符',
        email: '邮箱',
        email_placeholder: '请输入邮箱地址',
        verification_code: '验证码',
        code_placeholder: '请输入邮箱验证码',
        send_code: '发送验证码',
        password_hint: '至少6个字符',
        confirm_password: '确认密码',
        confirm_password_placeholder: '请再次输入密码',
        register_btn: '注 册',
        has_account: '已有账号？',
        back_to_login: '返回登录',

        // 提示消息
        logging_in: '登录中...',
        login_failed: '登录失败',
        network_error: '网络错误，请稍后重试',
        code_sent: '验证码已发送到您的邮箱',
        code_sent_hint: '验证码已发送，有效期10分钟',
        seconds_retry: '秒后重试',
        send_failed: '发送失败',
        passwords_not_match: '两次输入的密码不一致',
        enter_code: '请输入邮箱验证码',
        registering: '注册中...',
        register_success: '注册成功',
        register_success_msg: '您的账号已创建成功，请登录。',
        register_failed: '注册失败',
        enter_email_first: '请先输入邮箱地址',
        invalid_email: '邮箱格式不正确',
        enter_card_key_msg: '请输入卡密',
        recharging: '充值中...',
        recharge_failed: '充值失败',

        // 后端错误消息
        error_timeout: '图片生成超时，服务器繁忙，请稍后重试',
        error_quota_exceeded: 'API 配额已用尽，请稍后重试',
        error_service_unavailable: '服务暂时不可用，请稍后重试',
        error_server_busy: '服务器繁忙，请稍后重试',
        error_invalid_request: '请求参数无效，请检查提示词或图片',
        error_permission_denied: 'API 权限被拒绝，请联系管理员',
        error_invalid_input: '请求无效，请检查输入内容',
        error_generation_failed: '图片生成失败，请稍后重试',
        error_server_error: '服务器错误，请稍后重试或联系管理员',
        error_email_not_configured: '邮件服务未配置',
        error_email_required: '请输入邮箱地址',
        error_invalid_email: '邮箱格式不正确',
        error_email_auth_failed: '邮件服务认证失败',
        error_email_send_failed: '邮件发送失败，请稍后重试',

        // 通用
        btn_ok: '确定',
        btn_cancel: '取消',
        delete: '删除',
        confirm_delete_session: '确定要删除此会话吗？删除后无法恢复。',

        // main.js 消息
        upload_limit: '最多只能上传 {0} 张参考图',
        enter_prompt: '请输入提示词',
        generate_failed: '生成失败',
        generated_image: '生成的图片',
        reference_image: '参考图',
        settings_locked: '设置已锁定',
        settings_locked_msg: '更改模型、分辨率或纵横比会重置对话记忆，AI 将无法记住之前生成的图片。<br><br>如需使用不同设置，请点击确定创建新对话。',

        // 管理后台
        admin_page_title: '管理员控制台 - 码言旗下 Nano Banana',
        admin_title: '🛡️ 管理员控制台',
        admin_subtitle: '用户管理与数据监控',
        back_home: '← 返回主页',
        logout_btn: '退出登录',
        total_users: '总用户数',
        total_sessions: '总会话数',
        total_messages: '总消息数',
        total_admins: '管理员数',
        data_cleanup: '数据清理',
        quick_cleanup_desc: '快速清理：清理7天前的所有数据（包含图片、缩略图、孤儿文件）',
        cleanup_7days: '🗑️ 清理7天前数据',
        cleanup_all_desc: '清理所有数据：删除全部会话、图片、缩略图',
        cleanup_all: '🗑️ 清理所有数据',
        cleanup_all_title: '清理所有数据',
        cleanup_all_msg: '确定要清理所有数据吗？此操作将删除全部会话、图片和缩略图，且不可恢复！',
        custom_cleanup_desc: '自定义清理：清理指定日期前的所有数据（包含图片、缩略图、孤儿文件）',
        execute_cleanup: '🗑️ 执行清理',
        card_key_mgmt: '🔑 卡密管理',
        credits_per_card: '每张点数',
        generate_count: '生成数量',
        generate_keys: '🎫 生成卡密',
        security_tip: '🔒 安全提示：',
        security_tip_msg: '卡密使用哈希加密存储，生成后<strong>只显示一次</strong>，请立即保存！',
        card_key_code: '卡密码',
        credits: '点数',
        status: '状态',
        used_by: '使用者',
        created_at: '创建时间',
        actions: '操作',
        loading: '加载中...',
        user_list: '用户列表',
        id: 'ID',
        role: '角色',
        session_count: '会话数',
        message_count: '消息数',
        register_time: '注册时间',
        main_admin: '主管理员',
        admin: '管理员',
        normal_user: '普通用户',
        view_sessions: '查看会话',
        revoke_admin: '取消管理员',
        set_admin: '设为管理员',
        add_credits: '充值',
        delete_user: '删除',
        session_detail: '用户会话详情',
        session_list: '会话列表',
        no_sessions: '暂无会话',
        no_messages: '此会话暂无消息',
        select_session: '请在左侧选择一个会话查看详情',
        no_users: '暂无用户',
        no_cards: '暂无卡密',
        used: '已使用',
        available: '可用',
        permission_error: '权限错误',
        no_admin_permission: '您没有管理员权限',
        load_users_failed: '加载用户数据失败',
        load_sessions_failed: '加载会话失败',
        operation_success: '操作成功',
        operation_failed: '操作失败',
        unknown_error: '未知错误',
        confirm_delete_user: '确定要删除用户 "{0}" 吗？<br>此操作不可恢复，将删除该用户的所有数据！',
        user_deleted: '用户 {0} 已删除',
        delete_failed: '删除失败',
        credits_recharge: '点数充值',
        credits_recharge_prompt: '请输入要给用户 "{0}" 充值的点数（负数表示扣除）：',
        invalid_number: '请输入有效的数字',
        recharge_success: '充值成功',
        recharge_success_msg: '充值成功！用户现有 {0} 点',
        confirm_cleanup: '数据清理',
        confirm_cleanup_msg: '确定要清理 {0} 天前的所有数据吗？<br>此操作无法撤销！',
        select_date: '请选择日期',
        custom_cleanup: '自定义清理',
        custom_cleanup_msg: '确定要清理 {0} 之前的所有数据吗？<br>此操作无法撤销！',
        cleanup_complete: '清理完成',
        cleanup_failed: '清理失败',
        keys_generated: '🎫 卡密生成成功',
        save_keys_warning: '⚠️ 请立即保存这些卡密，关闭后将无法再查看完整卡密！',
        copy: '📋 复制',
        copied: '已复制',
        generate_failed_msg: '生成失败',
        key_copied: '卡密已复制到剪贴板',
        copy_failed: '复制失败，请手动复制',
        credits_must_range: '数量必须在1-100之间',
        invalid_credits: '请输入有效的点数',
        connect_error: '无法连接到服务器'
    },
    en: {
        // Page title
        page_title: 'GitSay Nano Banana AI Image Generator',

        // Top banner
        site_title: 'GitSay Nano',
        site_subtitle: 'Use Nano Banana Online',
        banner_brand: 'GitSay',
        banner_product: '🍌 Nano Banana',
        banner_desc: '4K AI Image Generator',
        banner_price: 'From $0.04/image',
        banner_trial: 'Free Trial',

        // User menu
        credits_label: 'credits',
        recharge_btn: '💳 Recharge',
        admin_panel: 'Admin Panel',
        logout: 'Logout',

        // Sidebar
        sidebar_brand: 'GitSay',
        new_chat: 'New Chat',
        messages_count: 'messages',
        close_menu: 'Close menu',
        open_menu: 'Open menu',

        // Control panel
        reference_images: 'Reference Images (Optional)',
        max_images_hint: 'Max 14',
        upload: 'Upload',
        upload_hint: 'Click or drag',
        upload_desc: 'Optional: Upload reference images. Support drag & drop or paste, max 14 images',
        prompt_label: 'Prompt',
        prompt_placeholder: 'e.g., A cute kitten sitting in a garden, oil painting style, HD, rich details',
        aspect_resolution: 'Model & Aspect Ratio & Resolution',
        resolution_label: 'Resolution (different resolutions cost different credits)',
        aspect_ratio_label: 'Aspect Ratio',
        model_label: 'AI Model',
        model_nano_banana_pro: 'Nano Banana Pro',
        model_nano_banana_pro_desc: 'Professional',
        model_nano_banana_2: 'Nano Banana 2',
        model_nano_banana_2_desc: 'Latest Model',
        aspect_auto: 'auto Adaptive',
        aspect_square: '1:1 Square',
        aspect_16_9: '16:9 Landscape',
        aspect_9_16: '9:16 Portrait',
        aspect_4_3: '4:3 Landscape',
        aspect_3_4: '3:4 Portrait',
        aspect_21_9: '21:9 Ultra-wide',
        aspect_3_2: '3:2 Landscape',
        aspect_2_3: '2:3 Portrait',
        settings_warning: '⚠️ Changing model, resolution or aspect ratio will reset chat memory, AI will not remember previously generated images',
        generate_btn: 'Generate Image',

        // Preview area
        chat_area: 'Chat Area',
        empty_state_title: 'Chat content and generated images will appear here',
        empty_state_hint: 'Enter a prompt on the left, click generate to start creating',
        click_to_view: '✨ Click image to view HD or download',

        // Loading state
        loading_text: 'Generating image...',
        loading_hint: 'Estimated time: 1 min',

        // Image preview modal
        image_preview: 'Image Preview',
        download_image: '📥 Download Image',

        // Recharge modal
        recharge_title: 'Credits Recharge',
        buy_card: 'Buy Card Key',
        buy_card_desc: 'Purchase credits card from the store',
        go_buy: 'Go Buy →',
        or: 'or',
        enter_card_key: 'Enter Card Key to Recharge',
        card_key_placeholder: 'Enter 16-digit card key',
        confirm_recharge: 'Confirm',
        current_credits: 'Current Credits: ',

        // Login/Register
        welcome_back: 'Welcome Back',
        login_subtitle: 'Login to GitSay Nano Banana',
        username: 'Username',
        username_placeholder: 'Enter username',
        password: 'Password',
        password_placeholder: 'Enter password',
        login_btn: 'Login',
        no_account: "Don't have an account?",
        register_now: 'Register Now',
        create_account: 'Create Account',
        register_subtitle: 'Join GitSay Nano Banana to start your AI journey',
        username_hint: 'At least 3 characters',
        email: 'Email',
        email_placeholder: 'Enter email address',
        verification_code: 'Verification Code',
        code_placeholder: 'Enter email verification code',
        send_code: 'Send Code',
        password_hint: 'At least 6 characters',
        confirm_password: 'Confirm Password',
        confirm_password_placeholder: 'Enter password again',
        register_btn: 'Register',
        has_account: 'Already have an account?',
        back_to_login: 'Back to Login',

        // Toast messages
        logging_in: 'Logging in...',
        login_failed: 'Login failed',
        network_error: 'Network error, please try again later',
        code_sent: 'Verification code sent to your email',
        code_sent_hint: 'Code sent, valid for 10 minutes',
        seconds_retry: 's to retry',
        send_failed: 'Failed to send',
        passwords_not_match: 'Passwords do not match',
        enter_code: 'Please enter verification code',
        registering: 'Registering...',
        register_success: 'Registration Successful',
        register_success_msg: 'Your account has been created. Please login.',
        register_failed: 'Registration failed',
        enter_email_first: 'Please enter email address first',
        invalid_email: 'Invalid email format',
        enter_card_key_msg: 'Please enter card key',
        recharging: 'Recharging...',
        recharge_failed: 'Recharge failed',

        // Backend error messages
        error_timeout: 'Image generation timed out, server busy, please try again later',
        error_quota_exceeded: 'API quota exceeded, please try again later',
        error_service_unavailable: 'Service temporarily unavailable, please try again later',
        error_server_busy: 'Server busy, please try again later',
        error_invalid_request: 'Invalid request parameters, please check prompt or image',
        error_permission_denied: 'API permission denied, please contact administrator',
        error_invalid_input: 'Invalid request, please check your input',
        error_generation_failed: 'Image generation failed, please try again later',
        error_server_error: 'Server error, please try again later or contact administrator',
        error_email_not_configured: 'Email service not configured',
        error_email_required: 'Please enter email address',
        error_invalid_email: 'Invalid email format',
        error_email_auth_failed: 'Email service authentication failed',
        error_email_send_failed: 'Failed to send email, please try again later',

        // Common
        btn_ok: 'OK',
        btn_cancel: 'Cancel',
        delete: 'Delete',
        confirm_delete_session: 'Are you sure you want to delete this session? This cannot be undone.',

        // main.js messages
        upload_limit: 'Maximum {0} reference images allowed',
        enter_prompt: 'Please enter a prompt',
        generate_failed: 'Generation failed',
        generated_image: 'Generated image',
        reference_image: 'Reference image',
        settings_locked: 'Settings Locked',
        settings_locked_msg: 'Changing model, resolution or aspect ratio will reset chat memory, AI will not remember previously generated images.<br><br>Click OK to create a new chat with different settings.',

        // Admin panel
        admin_page_title: 'Admin Console - GitSay Nano Banana',
        admin_title: '🛡️ Admin Console',
        admin_subtitle: 'GitSay · User Management & Data Monitoring',
        back_home: '← Back to Home',
        logout_btn: 'Logout',
        total_users: 'Total Users',
        total_sessions: 'Total Sessions',
        total_messages: 'Total Messages',
        total_admins: 'Admins',
        data_cleanup: 'Data Cleanup',
        quick_cleanup_desc: 'Quick cleanup: Clean all data older than 7 days (including images, thumbnails, orphan files)',
        cleanup_7days: '🗑️ Clean 7 Days Ago',
        cleanup_all_desc: 'Clean all data: Delete all sessions, images, and thumbnails',
        cleanup_all: '🗑️ Clean All Data',
        cleanup_all_title: 'Clean All Data',
        cleanup_all_msg: 'Are you sure you want to clean ALL data? This will delete all sessions, images and thumbnails. This action cannot be undone!',
        custom_cleanup_desc: 'Custom cleanup: Clean all data before specified date (including images, thumbnails, orphan files)',
        execute_cleanup: '🗑️ Execute Cleanup',
        card_key_mgmt: '🔑 Card Key Management',
        credits_per_card: 'Credits per card',
        generate_count: 'Quantity',
        generate_keys: '🎫 Generate Keys',
        security_tip: '🔒 Security Tip:',
        security_tip_msg: 'Card keys are stored with hash encryption. They are <strong>shown only once</strong> after generation, please save immediately!',
        card_key_code: 'Card Key',
        credits: 'Credits',
        status: 'Status',
        used_by: 'Used By',
        created_at: 'Created At',
        actions: 'Actions',
        loading: 'Loading...',
        user_list: 'User List',
        id: 'ID',
        role: 'Role',
        session_count: 'Sessions',
        message_count: 'Messages',
        register_time: 'Registered',
        main_admin: 'Main Admin',
        admin: 'Admin',
        normal_user: 'User',
        view_sessions: 'View Sessions',
        revoke_admin: 'Revoke Admin',
        set_admin: 'Set Admin',
        add_credits: 'Add Credits',
        delete_user: 'Delete',
        session_detail: 'User Session Details',
        session_list: 'Session List',
        no_sessions: 'No sessions',
        no_messages: 'No messages in this session',
        select_session: 'Select a session from the left to view details',
        no_users: 'No users',
        no_cards: 'No card keys',
        used: 'Used',
        available: 'Available',
        permission_error: 'Permission Error',
        no_admin_permission: 'You do not have admin permission',
        load_users_failed: 'Failed to load user data',
        load_sessions_failed: 'Failed to load sessions',
        operation_success: 'Operation successful',
        operation_failed: 'Operation failed',
        unknown_error: 'Unknown error',
        confirm_delete_user: 'Are you sure you want to delete user "{0}"?<br>This action cannot be undone and will delete all user data!',
        user_deleted: 'User {0} deleted',
        delete_failed: 'Delete failed',
        credits_recharge: 'Credits Recharge',
        credits_recharge_prompt: 'Enter credits to add for user "{0}" (negative to deduct):',
        invalid_number: 'Please enter a valid number',
        recharge_success: 'Recharge Successful',
        recharge_success_msg: 'Recharge successful! User now has {0} credits',
        confirm_cleanup: 'Data Cleanup',
        confirm_cleanup_msg: 'Are you sure you want to clean all data older than {0} days?<br>This action cannot be undone!',
        select_date: 'Please select a date',
        custom_cleanup: 'Custom Cleanup',
        custom_cleanup_msg: 'Are you sure you want to clean all data before {0}?<br>This action cannot be undone!',
        cleanup_complete: 'Cleanup Complete',
        cleanup_failed: 'Cleanup failed',
        keys_generated: '🎫 Card Keys Generated',
        save_keys_warning: '⚠️ Please save these keys immediately, they will not be shown again!',
        copy: '📋 Copy',
        copied: 'Copied',
        generate_failed_msg: 'Generation failed',
        key_copied: 'Card key copied to clipboard',
        copy_failed: 'Copy failed, please copy manually',
        credits_must_range: 'Quantity must be between 1-100',
        invalid_credits: 'Please enter valid credits',
        connect_error: 'Cannot connect to server'
    }
};

// ========================================
// I18n 类
// ========================================
class I18nManager {
    constructor() {
        this.currentLang = DEFAULT_LANG;
        this.listeners = [];
    }

    /**
     * 初始化 - 读取 localStorage 或使用默认语言
     */
    init() {
        const savedLang = localStorage.getItem('i18n_lang');
        if (savedLang && translations[savedLang]) {
            this.currentLang = savedLang;
        } else {
            this.currentLang = DEFAULT_LANG;
        }
        this.applyToPage();
        this.updateLangButtons();
        this.bindLangSwitch();
        return this;
    }

    /**
     * 获取翻译文本
     * @param {string} key - 翻译键
     * @param {...any} args - 替换参数 {0}, {1} 等
     */
    t(key, ...args) {
        let text = translations[this.currentLang]?.[key] || translations[DEFAULT_LANG]?.[key] || key;
        // 替换占位符 {0}, {1} 等
        args.forEach((arg, index) => {
            text = text.replace(new RegExp(`\\{${index}\\}`, 'g'), arg);
        });
        return text;
    }

    /**
     * 切换语言
     * @param {string} lang - 语言代码 'zh' 或 'en'
     */
    switchTo(lang) {
        if (!translations[lang]) return;
        this.currentLang = lang;
        localStorage.setItem('i18n_lang', lang);
        this.applyToPage();
        this.updateLangButtons();
        // 通知监听器
        this.listeners.forEach(fn => fn(lang));
    }

    /**
     * 获取当前语言
     */
    getLang() {
        return this.currentLang;
    }

    /**
     * 添加语言切换监听器
     */
    onLangChange(callback) {
        this.listeners.push(callback);
    }

    /**
     * 翻译后端错误消息
     * @param {string} errorMsg - 后端返回的错误消息或错误代码
     * @param {string} defaultKey - 如果无法翻译时使用的默认翻译键
     * @returns {string} 翻译后的错误消息
     */
    translateError(errorMsg, defaultKey = 'unknown_error') {
        if (!errorMsg) {
            return this.t(defaultKey);
        }
        // 如果是错误代码（以 error_ 开头），翻译它
        if (errorMsg.startsWith('error_')) {
            return this.t(errorMsg);
        }
        // 尝试作为翻译键翻译
        const translated = translations[this.currentLang]?.[errorMsg];
        if (translated) {
            return translated;
        }
        // 否则返回原始消息
        return errorMsg;
    }

    /**
     * 遍历页面中所有 data-i18n 属性的元素并应用翻译
     */
    applyToPage() {
        // 更新页面标题
        const titleKey = document.querySelector('title')?.getAttribute('data-i18n');
        if (titleKey) {
            document.title = this.t(titleKey);
        }

        // 更新 HTML lang 属性
        document.documentElement.lang = this.currentLang === 'zh' ? 'zh-CN' : 'en';

        // 遍历所有带 data-i18n 的元素
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (key) {
                // 检查是否有 data-i18n-attr 属性（用于设置 placeholder 等属性）
                const attr = el.getAttribute('data-i18n-attr');
                if (attr) {
                    el.setAttribute(attr, this.t(key));
                } else {
                    el.textContent = this.t(key);
                }
            }
        });

        // 更新带 data-i18n-placeholder 的元素
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (key) {
                el.placeholder = this.t(key);
            }
        });

        // 更新带 data-i18n-title 的元素
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (key) {
                el.title = this.t(key);
            }
        });

        // 更新带 data-i18n-html 的元素（允许HTML内容）
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            if (key) {
                el.innerHTML = this.t(key);
            }
        });
    }

    /**
     * 更新语言切换按钮状态
     */
    updateLangButtons() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const lang = btn.getAttribute('data-lang');
            btn.classList.toggle('active', lang === this.currentLang);
        });
    }

    /**
     * 绑定语言切换按钮事件
     */
    bindLangSwitch() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const lang = btn.getAttribute('data-lang');
                if (lang) {
                    this.switchTo(lang);
                }
            });
        });
    }
}

// 创建全局实例
window.I18n = new I18nManager();

// DOM 加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.I18n.init());
} else {
    window.I18n.init();
}
