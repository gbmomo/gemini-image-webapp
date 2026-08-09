"""
Gemini 图像生成网页应用
使用 Flask + Google Gemini API
支持多轮对话的图像生成和修改
"""

import os
import json
import uuid
import re
import base64
import binascii
import logging
import time
import threading
import ipaddress
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlsplit
from PIL import Image
import io
from filelock import FileLock, Timeout as FileLockTimeout
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from google import genai
from google.genai import types, errors as genai_errors
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_compress import Compress

# 加载 .env 文件中的环境变量（必须在导入 email_service 之前）
load_dotenv()

# 配置日志（根据环境动态设置级别）
_log_level = logging.DEBUG if os.getenv('FLASK_ENV') != 'production' else logging.INFO
logging.basicConfig(level=_log_level)
logger = logging.getLogger(__name__)

# 导入需要环境变量的模块
from database import (
    cleanup_expired_codes,
    create_verification_code,
    delete_user,
    delete_verification_code,
    generate_card_keys,
    get_active_api_settings,
    get_all_card_keys,
    get_all_users,
    get_model_pricing,
    get_stale_generation_charges,
    get_user_by_id,
    register_user_with_verification_code,
    reserve_generation_credits,
    resolve_generation_charge,
    save_api_settings,
    save_model_pricing,
    toggle_admin,
    update_user_credits,
    use_card_key,
    verify_user,
)
from email_service import generate_verification_code, send_verification_email
from werkzeug.security import generate_password_hash

UNSAFE_SECRET_KEYS = {
    "your_random_secret_key_here",
    "请替换为高强度随机字符串",
    "change-me",
    "changeme",
}


def _validated_secret_key():
    secret_key = (os.getenv("SECRET_KEY") or "").strip()
    if not secret_key:
        raise ValueError("请设置环境变量 SECRET_KEY 或在 .env 文件中配置")
    if secret_key.lower() in UNSAFE_SECRET_KEYS or len(secret_key.encode("utf-8")) < 32:
        raise ValueError("SECRET_KEY 不能使用示例值，且必须至少包含 32 字节的随机数据")
    return secret_key


app = Flask(__name__, static_folder=None)
app.secret_key = _validated_secret_key()

_trust_proxy_count = int(os.getenv("TRUST_PROXY_COUNT", "0"))
if _trust_proxy_count > 0:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=_trust_proxy_count,
        x_proto=_trust_proxy_count,
        x_host=_trust_proxy_count,
    )

# Session 安全配置
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # 生产环境启用HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF保护
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session过期时间

# CSRF 与请求体保护配置
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_REQUEST_BYTES', 50 * 1024 * 1024))
csrf = CSRFProtect(app)

# 速率限制配置
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://")
)

# Gzip 压缩配置（优化网络传输）
app.config['COMPRESS_MIMETYPES'] = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript',
    'text/javascript',
]
app.config['COMPRESS_LEVEL'] = 6  # 压缩级别 1-9，6是平衡速度和压缩率
app.config['COMPRESS_MIN_SIZE'] = 500  # 只压缩大于500字节的响应
compress = Compress()
compress.init_app(app)

# 速率限制错误返回 JSON 格式
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "请求过于频繁，请稍后再试"}), 429


@app.errorhandler(413)
def request_too_large_handler(e):
    return jsonify({"error": "请求体过大，请压缩参考图片后重试"}), 413


@app.errorhandler(CSRFError)
def csrf_error_handler(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "页面验证已失效，请刷新后重试"}), 400
    return e.description, 400


@app.errorhandler(FileLockTimeout)
def file_lock_timeout_handler(e):
    logger.warning("等待文件锁超时: %s", e)
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "请求正在处理中，请稍后重试",
            "error_code": "LOCK_TIMEOUT",
        }), 503
    return "请求正在处理中，请稍后重试", 503


@app.after_request
def prevent_sensitive_api_caching(response):
    if request.path.startswith("/api/admin/") or request.path.startswith("/api/sessions"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


# 安全响应头（仅在生产环境启用HTTPS强制）
if os.getenv('FLASK_ENV') == 'production':
    Talisman(app, 
             force_https=True,
             strict_transport_security=True,
             content_security_policy={
                 'default-src': "'self'",
                 'script-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
                 'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
                 'font-src': ["'self'", "https://fonts.gstatic.com"],
                 'img-src': ["'self'", "data:"],
             })

# 获取默认模型的辅助函数
def get_default_model():
    db_settings = get_active_api_settings()
    if db_settings and db_settings.get("default_model") in ALLOWED_MODELS:
        return db_settings["default_model"]
    env_default = os.getenv("DEFAULT_MODEL")
    if env_default in ALLOWED_MODELS:
        return env_default
    return "gemini-3.1-flash-image"

DATA_DIR = os.getenv("DATA_DIR", "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
IMAGES_DIR = os.getenv("IMAGES_DIR", "static/images")
THUMBNAILS_DIR = os.getenv("THUMBNAILS_DIR", "static/thumbnails")
MAINTENANCE_LOCK_FILE = os.path.join(DATA_DIR, ".maintenance.lock")

# 官方模型能力矩阵（https://ai.google.dev/gemini-api/docs/image-generation）。
# 前端选项、请求验证与后台定价均从这一处派生，避免规则漂移。
COMMON_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
MODEL_CAPABILITIES = {
    "gemini-3.1-flash-lite-image": {
        "name": "Nano Banana 2 Lite", "sizes": ["1K"], "ratios": COMMON_RATIOS, "max_references": 14,
    },
    "gemini-3.1-flash-image": {
        "name": "Nano Banana 2", "sizes": ["512", "1K", "2K", "4K"],
        "ratios": ["1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"],
        "max_references": 14,
    },
    "gemini-3-pro-image": {
        "name": "Nano Banana Pro", "sizes": ["1K", "2K", "4K"], "ratios": COMMON_RATIOS, "max_references": 14,
    },
    "gemini-2.5-flash-image": {
        "name": "Nano Banana", "sizes": ["1K"], "ratios": COMMON_RATIOS, "max_references": 3,
    },
}
ALLOWED_MODELS = {model_id: config["name"] for model_id, config in MODEL_CAPABILITIES.items()}
DEFAULT_PRICES = {"512": 1, "1K": 1, "2K": 2, "4K": 4}
MAX_PROMPT_LENGTH = 100000  # 支持长提示词
MAX_REFERENCE_IMAGES = 14
MAX_REFERENCE_IMAGE_BYTES = int(os.getenv("MAX_REFERENCE_IMAGE_BYTES", 10 * 1024 * 1024))
MAX_REFERENCE_TOTAL_BYTES = int(os.getenv("MAX_REFERENCE_TOTAL_BYTES", 35 * 1024 * 1024))
MAX_REFERENCE_PIXELS = int(os.getenv("MAX_REFERENCE_PIXELS", 40_000_000))
GENERATION_CHARGE_TTL_SECONDS = max(
    600, int(os.getenv("GENERATION_CHARGE_TTL_SECONDS", "900"))
)
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico'}
PIL_ALLOWED_FORMATS = ("PNG", "JPEG", "GIF", "WEBP", "ICO")
REFERENCE_FORMATS = {
    "PNG": ("image/png", ".png"),
    "JPEG": ("image/jpeg", ".jpg"),
    "GIF": ("image/gif", ".gif"),
    "WEBP": ("image/webp", ".webp"),
    "ICO": ("image/x-icon", ".ico"),
}


def _harden_private_path(path, mode):
    if os.name != "posix" or not os.path.exists(path):
        return
    try:
        os.chmod(path, mode)
    except OSError as exc:
        logger.warning("无法收紧敏感路径权限: %s", exc)


# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
for private_directory in (DATA_DIR, SESSIONS_DIR, IMAGES_DIR, THUMBNAILS_DIR):
    _harden_private_path(private_directory, 0o700)

# 静态文件版本号（用于缓存刷新，每次启动时更新）
APP_VERSION = str(int(time.time()))

@app.context_processor
def inject_version():
    """向所有模板注入版本号，用于静态文件缓存刷新"""
    return {"v": APP_VERSION}


def _validate_custom_base_url(base_url):
    """限制自定义端点为无内嵌凭据的 HTTP(S) URL。"""
    if not isinstance(base_url, str) or not base_url or len(base_url) > 2048:
        return "自定义 API 端点 URL 无效"
    try:
        parsed = urlsplit(base_url)
        parsed_port = parsed.port
    except ValueError:
        return "自定义 API 端点 URL 无效"
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "自定义 API 端点只允许 http 或 https URL"
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return "自定义 API 端点不能包含账号、密码、查询参数或片段"
    if parsed_port is not None and not 1 <= parsed_port <= 65535:
        return "自定义 API 端点端口必须在 1 到 65535 之间"
    if os.getenv("FLASK_ENV") == "production" and parsed.scheme != "https":
        hostname = parsed.hostname.lower()
        is_loopback = hostname == "localhost"
        try:
            is_loopback = is_loopback or ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            pass
        if not is_loopback:
            return "生产环境仅允许 HTTPS 自定义端点；本机回环地址除外"
    return None


# ========================================
# Gemini 客户端（动态配置，支持多种 Provider）
# ========================================

def _build_genai_client(provider, api_key, custom_base_url=None):
    """根据 provider 类型构建 genai.Client 实例"""
    http_options = types.HttpOptions(timeout=300000)  # 300秒超时

    if provider == 'custom':
        validation_error = _validate_custom_base_url(custom_base_url)
        if validation_error:
            raise ValueError(validation_error)
        endpoint = urlsplit(custom_base_url)
        hostname = endpoint.hostname or ""
        if ":" in hostname:
            hostname = f"[{hostname}]"
        safe_origin = f"{endpoint.scheme}://{hostname}"
        if endpoint.port:
            safe_origin += f":{endpoint.port}"
        logger.info("使用自定义 API 端点: %s", safe_origin)
        http_options = types.HttpOptions(timeout=300000, base_url=custom_base_url)
        return genai.Client(api_key=api_key, http_options=http_options)
    else:  # google_ai（默认）
        logger.info("使用 Google AI Studio 模式")
        return genai.Client(api_key=api_key, http_options=http_options)


def _resolve_client_settings():
    """返回当前客户端配置及跨 worker 可比较的版本签名。"""
    db_settings = get_active_api_settings()
    if db_settings:
        settings = {
            "provider": db_settings["provider"],
            "api_key": db_settings["api_key"],
            "custom_base_url": db_settings.get("custom_base_url"),
        }
        signature = (
            "db",
            db_settings.get("id"),
            db_settings.get("updated_at"),
            settings["provider"],
            settings["custom_base_url"],
        )
        return settings, signature

    env_api_key = os.getenv("GEMINI_API_KEY")
    env_base_url = os.getenv("GEMINI_API_BASE_URL")
    if env_api_key:
        provider = 'custom' if env_base_url else 'google_ai'
        settings = {
            "provider": provider,
            "api_key": env_api_key,
            "custom_base_url": env_base_url,
        }
        return settings, ("env", provider, env_api_key, env_base_url)

    return None, None


def _init_client():
    """按数据库优先、环境变量回退的顺序初始化 Gemini 客户端。"""
    settings, signature = _resolve_client_settings()
    if settings:
        source = "数据库" if signature[0] == "db" else "环境变量"
        logger.info(f"从{source}加载 API 设置 (provider: {settings['provider']})")
        return (
            _build_genai_client(
                settings["provider"],
                settings["api_key"],
                settings["custom_base_url"],
            ),
            signature,
        )

    logger.warning("⚠️ 未找到 API 配置！请在管理员后台设置 API Key，或在 .env 文件中配置 GEMINI_API_KEY")
    return None, None


client_lock = threading.Lock()  # 客户端重建时的线程安全锁
client, client_config_signature = _init_client()


def reload_client():
    """重建 Gemini 客户端（管理员更改 API 设置后调用）"""
    global client, client_config_signature
    with client_lock:
        new_client, new_signature = _init_client()
        if new_client:
            client = new_client
            client_config_signature = new_signature
            # 清除所有活跃聊天会话（client 变了，旧的 chat 对象不可用）
            with active_chats_lock:
                count = len(active_chats)
                active_chats.clear()
            logger.info(f"Gemini 客户端已重建，已清除 {count} 个活跃会话")
            return True
        return False


def ensure_client_current():
    """在每次生成前检测数据库版本，确保所有 worker 最终使用同一配置。"""
    global client, client_config_signature
    _, current_signature = _resolve_client_settings()
    if current_signature == client_config_signature:
        return client is not None
    return reload_client()

# 存储活跃的聊天会话（内存中）
active_chats = {}
active_chats_lock = threading.Lock()  # 线程安全锁

# 自动清理长时间未使用的聊天会话，释放内存
# 用户回来时会通过 rebuild_chat_history 从 JSON 自动重建
CHAT_IDLE_TIMEOUT = int(os.getenv("CHAT_IDLE_TIMEOUT", 1800))  # 默认30分钟（秒）
CHAT_CLEANUP_INTERVAL = int(os.getenv("CHAT_CLEANUP_INTERVAL", 600))  # 默认10分钟检查一次

def cleanup_inactive_chats():
    """后台线程：定期清理长时间未使用的聊天会话，释放内存，并清理过期验证码"""
    while True:
        try:
            time.sleep(CHAT_CLEANUP_INTERVAL)
            now = time.time()
            with active_chats_lock:
                expired = [sid for sid, data in active_chats.items() 
                          if now - data.get('last_access', 0) > CHAT_IDLE_TIMEOUT]
                for sid in expired:
                    del active_chats[sid]
            if expired:
                logger.info(f"已清理 {len(expired)} 个闲置聊天会话")
            
            # 定期清理过期的邮箱验证码
            try:
                deleted = cleanup_expired_codes()
                if deleted > 0:
                    logger.info(f"已清理 {deleted} 条过期验证码")
            except Exception as e:
                logger.error(f"清理过期验证码失败: {e}")
            reconcile_charges = globals().get("reconcile_stale_generation_charges")
            if reconcile_charges:
                try:
                    resolved = reconcile_charges()
                    if resolved:
                        logger.info(f"已对账 {resolved} 笔过期生成扣费")
                except Exception as e:
                    logger.error(f"生成扣费后台对账失败: {e}")
        except Exception as e:
            logger.error(f"清理线程错误: {e}")
            time.sleep(60)  # 错误后等待60秒再重试，避免循环崩溃

cleanup_thread = None
if os.getenv("DISABLE_BACKGROUND_TASKS", "false").lower() != "true":
    cleanup_thread = threading.Thread(target=cleanup_inactive_chats, daemon=True)
    cleanup_thread.start()
    logger.info(f"会话自动清理已启动（闲置超时: {CHAT_IDLE_TIMEOUT}s, 检查间隔: {CHAT_CLEANUP_INTERVAL}s）")


def _clear_authentication_session():
    """移除登录状态，但保留 CSRF token 等非认证 session 数据。"""
    for key in ("user_id", "username", "is_admin"):
        session.pop(key, None)


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        user = get_user_by_id(user_id) if user_id is not None else None
        if user is None:
            _clear_authentication_session()
            # 如果是 API 请求，返回 JSON 错误
            if request.path.startswith("/api/"):
                return jsonify({"error": "请先登录"}), 401
            return redirect(url_for("login"))
        session["username"] = user["username"]
        session["is_admin"] = user["is_admin"]
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        user = get_user_by_id(user_id) if user_id is not None else None
        if user is None:
            _clear_authentication_session()
            if request.path.startswith("/api/"):
                return jsonify({"error": "请先登录"}), 401
            return redirect(url_for("login"))
        session["username"] = user["username"]
        session["is_admin"] = user["is_admin"]
        if not user["is_admin"]:
            if request.path.startswith("/api/"):
                return jsonify({"error": "需要管理员权限"}), 403
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def get_user_sessions_file(user_id):
    """获取用户的会话文件路径"""
    return os.path.join(SESSIONS_DIR, f"user_{user_id}.json")



def _get_session_lock(user_id):
    """获取用户会话文件的文件锁"""
    sessions_file = get_user_sessions_file(user_id)
    return FileLock(sessions_file + ".lock", timeout=10)


def _get_generation_lock(session_id):
    """跨线程、跨 worker 串行化同一聊天会话的生成请求。"""
    return FileLock(
        os.path.join(SESSIONS_DIR, f".chat_{session_id}.lock"),
        timeout=int(os.getenv("GENERATION_LOCK_TIMEOUT", "330")),
    )


def _get_maintenance_lock():
    """协调文件落盘与管理员孤儿文件清理。"""
    return FileLock(MAINTENANCE_LOCK_FILE, timeout=30)


def _load_sessions_unlocked(user_id):
    """调用方持有用户锁时读取会话文件。"""
    sessions_file = get_user_sessions_file(user_id)
    if not os.path.exists(sessions_file):
        return {}
    try:
        with open(sessions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"会话文件损坏 (user {user_id}): {e}")
        backup_file = f"{sessions_file}.corrupt.{int(time.time())}"
        try:
            import shutil
            shutil.copy2(sessions_file, backup_file)
            logger.info(f"已备份损坏的会话文件到: {backup_file}")
        except Exception as backup_error:
            logger.error(f"备份失败: {backup_error}")
        try:
            os.remove(sessions_file)
        except Exception as remove_error:
            logger.error(f"删除损坏文件失败: {remove_error}")
        return {}


def _save_sessions_unlocked(user_id, sessions):
    """调用方持有用户锁时原子写入会话文件。"""
    sessions_file = get_user_sessions_file(user_id)
    tmp_file = f"{sessions_file}.{uuid.uuid4().hex}.tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        _harden_private_path(tmp_file, 0o600)
        os.replace(tmp_file, sessions_file)
        _harden_private_path(sessions_file, 0o600)
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


def load_sessions(user_id):
    """加载指定用户的会话数据（带文件锁防止并发问题）"""
    with _get_session_lock(user_id):
        return _load_sessions_unlocked(user_id)


def save_sessions(user_id, sessions):
    """保存指定用户的会话数据（原子写入 + 文件锁，防止并发和文件损坏）"""
    with _get_session_lock(user_id):
        _save_sessions_unlocked(user_id, sessions)


def _delete_message_files(msg):
    """删除消息关联的所有图片文件（生成图片、缩略图、参考图片）"""
    # 删除生成的图片
    if msg.get("image"):
        image_path = os.path.join(IMAGES_DIR, os.path.basename(msg["image"]))
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                logger.warning(f"删除图片失败 {image_path}: {e}")
    # 删除缩略图
    if msg.get("thumbnail"):
        thumb_path = os.path.join(THUMBNAILS_DIR, os.path.basename(msg["thumbnail"]))
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception as e:
                logger.warning(f"删除缩略图失败 {thumb_path}: {e}")
    # 删除参考图片
    if msg.get("reference_images"):
        for ref_img in msg["reference_images"]:
            ref_path = os.path.join(IMAGES_DIR, os.path.basename(ref_img))
            if os.path.exists(ref_path):
                try:
                    os.remove(ref_path)
                except Exception as e:
                    logger.warning(f"删除参考图片失败 {ref_path}: {e}")


def _get_json_data():
    """安全获取 JSON 对象；数组、标量和无效 JSON 均按空对象处理。"""
    try:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _validate_session_id(session_id):
    """验证 session_id 是否是合法的 UUID 格式"""
    try:
        uuid.UUID(session_id)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def create_thumbnail(image_path, thumbnail_filename, max_size=400, quality=60):
    """
    创建缩略图用于预览加载
    Args:
        image_path: 原始图片路径
        thumbnail_filename: 缩略图文件名
        max_size: 缩略图最大边长（像素）
        quality: JPEG压缩质量 (1-100)
    Returns:
        缩略图的URL路径
    """
    thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)
    try:
        with Image.open(image_path, formats=PIL_ALLOWED_FORMATS) as img:
            # 转换为RGB模式（如果是RGBA等）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 计算缩放比例，保持宽高比
            ratio = min(max_size / img.width, max_size / img.height)
            if ratio < 1:  # 只有图片比max_size大时才缩小
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式以获得更好的压缩
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            _harden_private_path(thumbnail_path, 0o600)
            
            return f"/static/thumbnails/{thumbnail_filename}"
    except Exception as e:
        try:
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except OSError as cleanup_error:
            logger.warning(f"清理未完成的缩略图失败 {thumbnail_path}: {cleanup_error}")
        logger.warning(f"创建缩略图失败: {e}")
        return None


def rebuild_chat_history(user_id, session_id):
    """从保存的消息历史重建 Gemini Chat 的 history 参数"""
    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return []
    
    messages = sessions[session_id].get("messages", [])
    if not messages:
        return []
    
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    
    history = []
    for msg in messages:
        parts = []
        role = msg.get("role", "user")
        
        if role == "user":
            # 添加参考图片
            ref_images = msg.get("reference_images") or []
            for ref_img in ref_images:
                ref_path = os.path.join(IMAGES_DIR, os.path.basename(ref_img))
                if os.path.exists(ref_path):
                    try:
                        with open(ref_path, "rb") as f:
                            image_data = f.read()
                        ext = os.path.splitext(ref_path)[1].lower()
                        mime_type = mime_map.get(ext, 'image/png')
                        parts.append(types.Part.from_bytes(
                            data=image_data, mime_type=mime_type
                        ))
                    except Exception as e:
                        logger.warning(f"重建历史时加载参考图片失败 {ref_img}: {e}")
            
            # 添加文本
            if msg.get("content"):
                parts.append(types.Part(text=msg["content"]))
            
            if parts:
                history.append(types.Content(role="user", parts=parts))
        
        elif role == "assistant":
            # 添加文本
            if msg.get("content"):
                text_part = types.Part(text=msg["content"])
                # 附加文本部分的 thought_signature（Gemini API 多轮对话必需）
                if msg.get("text_thought_signature"):
                    signature = msg["text_thought_signature"]
                    if isinstance(signature, str):
                        signature = base64.b64decode(signature)
                    text_part.thought_signature = signature
                parts.append(text_part)
            
            # 添加生成的图片
            if msg.get("image"):
                image_filename = os.path.basename(msg["image"])
                image_path = os.path.join(IMAGES_DIR, image_filename)
                if os.path.exists(image_path):
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()
                        ext = os.path.splitext(image_path)[1].lower()
                        mime_type = mime_map.get(ext, 'image/png')
                        
                        # 创建图片部分
                        image_part = types.Part.from_bytes(
                            data=image_data, mime_type=mime_type
                        )

                        # 附加图片部分的 thought_signature（Gemini API 多轮对话必需）
                        if msg.get("thought_signature"):
                            signature = msg["thought_signature"]
                            if isinstance(signature, str):
                                signature = base64.b64decode(signature)
                            image_part.thought_signature = signature

                        parts.append(image_part)
                    except Exception as e:
                        logger.warning(f"重建历史时加载生成图片失败 {msg['image']}: {e}")
            
            if parts:
                history.append(types.Content(role="model", parts=parts))
    
    return history


def create_chat(
    session_id,
    aspect_ratio="auto",
    image_size="2K",
    model=None,
    user_id=None,
    history_version=None,
):
    """创建新的聊天实例，如果有历史消息则自动恢复上下文"""
    model = model or get_default_model()
    # 本项目使用 Generate Content 的 chats API；response_format 仅属于
    # Interactions API，不能传给 GenerateContentConfig。
    image_config = types.ImageConfig(image_size=image_size)
    if aspect_ratio != "auto":
        image_config.aspect_ratio = aspect_ratio
    config = types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=image_config,
    )
    
    # 从保存的消息历史重建 Chat 上下文
    history = []
    if user_id:
        try:
            history = rebuild_chat_history(user_id, session_id)
            if history:
                logger.info(f"为会话 {session_id} 重建了 {len(history)} 条历史消息")
        except Exception as e:
            logger.error(f"重建聊天历史失败: {e}", exc_info=True)
            history = []
    
    chat = client.chats.create(model=model, config=config, history=history)
    with active_chats_lock:
        active_chats[session_id] = {
            "chat": chat,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "model": model,
            "history_version": history_version,
            "last_access": time.time()
        }
    return chat


def get_or_create_chat(
    session_id,
    aspect_ratio="auto",
    image_size="2K",
    model=None,
    user_id=None,
    history_version=None,
):
    """获取或创建聊天实例"""
    model = model or get_default_model()
    with active_chats_lock:
        if session_id in active_chats:
            chat_data = active_chats[session_id]
            chat_data["last_access"] = time.time()  # 更新最后访问时间
            # 如果配置变了，重新创建
            if (chat_data["aspect_ratio"] != aspect_ratio or 
                chat_data["image_size"] != image_size or 
                chat_data.get("model") != model or
                chat_data.get("history_version") != history_version):
                pass  # 需要重建，退出锁后处理
            else:
                return chat_data["chat"]
    return create_chat(
        session_id,
        aspect_ratio,
        image_size,
        model,
        user_id,
        history_version,
    )


@app.route("/")
def index():
    """主页"""
    user = None
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
        if user is None:
            _clear_authentication_session()
    return render_template("index.html", user=user, default_model=get_default_model())


@app.route("/api/models", methods=["GET"])
def get_models():
    """获取可用的图像生成模型列表"""
    default_model = get_default_model()
    pricing = get_model_pricing()
    models = [{
        "id": model_id,
        "name": config["name"],
        "default": model_id == default_model,
        "sizes": [{"id": size, "credits": pricing.get((model_id, size), DEFAULT_PRICES[size])}
                  for size in config["sizes"]],
        "ratios": config["ratios"],
        "max_references": config["max_references"],
    } for model_id, config in MODEL_CAPABILITIES.items()]
    return jsonify({"models": models, "default": default_model})


@app.route("/login")
def login():
    """登录页（重定向到主页，主页自带登录功能）"""
    return redirect(url_for("index"))




@app.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")  # 防止暴力破解
def api_login():
    """登录接口"""
    data = _get_json_data()
    username = data.get("username", "")
    password = data.get("password", "")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "用户名或密码错误"}), 400
    if len(username) > 64 or len(password) > 256:
        return jsonify({"error": "用户名或密码错误"}), 400
    
    success, message, user = verify_user(username, password)
    
    if success:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = user.get("is_admin", False)
        return jsonify({"success": True, "message": message, "is_admin": user.get("is_admin", False)})
    else:
        return jsonify({"error": message}), 401


@app.route("/api/send-verification-code", methods=["POST"])
@limiter.limit("1 per minute")  # 防止滥用
def send_verification_code_route():
    """发送邮箱验证码"""
    data = _get_json_data()
    email_value = data.get("email", "")
    if not isinstance(email_value, str):
        return jsonify({"error": "error_invalid_email"}), 400
    email = email_value.strip()
    
    if not email:
        return jsonify({"error": "error_email_required"}), 400
    if len(email) > 254:
        return jsonify({"error": "error_invalid_email"}), 400
    
    # 验证邮箱格式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"error": "error_invalid_email"}), 400
    
    # 生成验证码
    code = generate_verification_code(6)
    code_hash = generate_password_hash(code)
    
    # 设置过期时间（10分钟）
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
    
    # 保存到数据库
    success, message = create_verification_code(email, code_hash, expires_at)
    if not success:
        return jsonify({"error": message}), 500
    
    # 发送邮件
    success, message = send_verification_email(email, code)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        try:
            delete_verification_code(email, code_hash)
        except Exception as exc:
            logger.error(f"回滚发送失败的验证码记录时出错: {exc}")
        return jsonify({"error": message}), 500


@app.route("/api/register", methods=["POST"])
@limiter.limit("3 per hour")  # 防止批量注册
def api_register():
    """注册接口"""
    data = _get_json_data()
    username = data.get("username", "")
    email_value = data.get("email", "")
    password = data.get("password", "")
    verification_code_value = data.get("verification_code", "")
    if not isinstance(email_value, str) or not isinstance(verification_code_value, str):
        return jsonify({"error": "邮箱或验证码格式无效"}), 400
    email = email_value.strip()
    verification_code = verification_code_value.strip()
    
    # 验证邮箱和验证码
    if not email or not verification_code:
        return jsonify({"error": "请输入邮箱和验证码"}), 400
    if len(email) > 254 or len(verification_code) != 6 or not verification_code.isdigit():
        return jsonify({"error": "邮箱或验证码格式无效"}), 400
    
    success, message, user_id = register_user_with_verification_code(
        username,
        password,
        email,
        verification_code,
    )
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    """登出接口"""
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/sessions", methods=["GET"])
@login_required
def get_sessions():
    """获取当前用户的所有会话列表"""
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    session_list = []
    for sid, data in sessions.items():
        session_list.append({
            "id": sid,
            "title": data.get("title", "新对话"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "message_count": len(data.get("messages", []))
        })
    # 按更新时间排序
    session_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return jsonify(session_list)


@app.route("/api/sessions", methods=["POST"])
@login_required
def create_session_route():
    """创建新会话"""
    user_id = session["user_id"]
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _get_session_lock(user_id):
        if get_user_by_id(user_id) is None:
            _clear_authentication_session()
            return jsonify({"error": "请先登录"}), 401
        sessions = _load_sessions_unlocked(user_id)
        sessions[session_id] = {
            "title": "新对话",
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "settings": None
        }
        _save_sessions_unlocked(user_id, sessions)
    return jsonify({
        "id": session_id,
        "title": "新对话",
        "created_at": now,
        "updated_at": now,
        "message_count": 0
    })


@app.route("/api/sessions/<session_id>", methods=["GET"])
@login_required
def get_session_route(session_id):
    """获取单个会话详情"""
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404
    session_data = sessions[session_id]

    # 过滤掉 thought_signature，前端不需要，避免传输大量数据
    filtered_messages = []
    for msg in session_data.get("messages", []):
        filtered_msg = {
            k: v for k, v in msg.items()
            if k not in (
                "thought_signature", "text_thought_signature", "generation_charge_id",
            )
        }
        filtered_messages.append(filtered_msg)

    return jsonify({
        "id": session_id,
        "title": session_data.get("title"),
        "created_at": session_data.get("created_at"),
        "updated_at": session_data.get("updated_at"),
        "messages": filtered_messages,
        "settings": session_data.get("settings"),
    })


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
@login_required
def delete_session_route(session_id):
    """删除会话"""
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    user_id = session["user_id"]
    deleted_messages = []
    with _get_generation_lock(session_id):
        with _get_maintenance_lock():
            with _get_session_lock(user_id):
                sessions = _load_sessions_unlocked(user_id)
                if session_id in sessions:
                    deleted_messages = sessions[session_id].get("messages", [])
                    del sessions[session_id]
                    _save_sessions_unlocked(user_id, sessions)
            for msg in deleted_messages:
                _delete_message_files(msg)
            with active_chats_lock:
                active_chats.pop(session_id, None)
    return jsonify({"success": True})


@app.route("/api/sessions/<session_id>/title", methods=["PUT"])
@login_required
def update_session_title(session_id):
    """更新会话标题"""
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    user_id = session["user_id"]
    data = _get_json_data()
    title = data.get("title", "新对话")
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        return jsonify({"error": "标题必须为 1 到 200 个字符"}), 400
    with _get_session_lock(user_id):
        if get_user_by_id(user_id) is None:
            _clear_authentication_session()
            return jsonify({"error": "请先登录"}), 401
        sessions = _load_sessions_unlocked(user_id)
        if session_id not in sessions:
            return jsonify({"error": "会话不存在"}), 404
        sessions[session_id]["title"] = title.strip()
        sessions[session_id]["updated_at"] = datetime.now().isoformat()
        _save_sessions_unlocked(user_id, sessions)
    return jsonify({"success": True})




def _validate_generate_params(data):
    """验证图像生成请求参数，无效时返回错误响应元组"""
    session_id = data.get("session_id")
    prompt = data.get("prompt", "")
    aspect_ratio = data.get("aspect_ratio", "auto")
    image_size = data.get("image_size", "2K")
    model = data.get("model") or get_default_model()
    reference_images = data.get("reference_images", [])

    if not isinstance(session_id, str) or not session_id or not isinstance(prompt, str) or not prompt:
        return jsonify({"error": "缺少必要参数"}), 400
    if not isinstance(model, str) or model not in ALLOWED_MODELS:
        return jsonify({"error": "无效的模型参数"}), 400
    if not isinstance(aspect_ratio, str):
        return jsonify({"error": "无效的纵横比参数"}), 400
    if not isinstance(image_size, str):
        return jsonify({"error": "无效的分辨率参数"}), 400
    if not isinstance(reference_images, list) or any(not isinstance(image, str) for image in reference_images):
        return jsonify({"error": "参考图片参数格式无效"}), 400
    capabilities = MODEL_CAPABILITIES[model]
    # auto 只用于兼容历史会话；新界面只会提交模型明确支持的比例。
    if aspect_ratio != "auto" and aspect_ratio not in capabilities["ratios"]:
        return jsonify({"error": f"{capabilities['name']} 不支持该纵横比"}), 400
    if image_size not in capabilities["sizes"]:
        return jsonify({"error": f"{capabilities['name']} 不支持 {image_size} 分辨率"}), 400
    if len(prompt.strip()) == 0:
        return jsonify({"error": "提示词不能为空"}), 400
    if len(prompt) > MAX_PROMPT_LENGTH:
        return jsonify({"error": f"提示词过长，最多{MAX_PROMPT_LENGTH}字符"}), 400
    if len(reference_images) > capabilities["max_references"]:
        return jsonify({"error": f"{capabilities['name']} 最多支持 {capabilities['max_references']} 张参考图"}), 400
    max_encoded_size = (MAX_REFERENCE_IMAGE_BYTES * 4 // 3) + 1024
    if any(len(image) > max_encoded_size for image in reference_images):
        return jsonify({"error": f"单张参考图片不能超过 {MAX_REFERENCE_IMAGE_BYTES // (1024 * 1024)} MB"}), 400
    return None


class ReferenceImageError(ValueError):
    pass


def _process_reference_images(reference_images, session_id, message_index):
    """校验并解码参考图；成功生成后再统一落盘。"""
    contents = []
    decoded_images = []
    total_bytes = 0
    for i, ref_image in enumerate(reference_images):
        if not ref_image:
            continue
        image_data = ref_image
        if "," in image_data:
            header, image_data = image_data.split(",", 1)
            if not header.startswith("data:image/") or ";base64" not in header.lower():
                raise ReferenceImageError("参考图片 Data URL 格式无效")
        try:
            decoded = base64.b64decode(image_data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ReferenceImageError("参考图片 Base64 数据无效") from exc
        if not decoded or len(decoded) > MAX_REFERENCE_IMAGE_BYTES:
            raise ReferenceImageError(
                f"单张参考图片不能超过 {MAX_REFERENCE_IMAGE_BYTES // (1024 * 1024)} MB"
            )
        total_bytes += len(decoded)
        if total_bytes > MAX_REFERENCE_TOTAL_BYTES:
            raise ReferenceImageError(
                f"参考图片总大小不能超过 {MAX_REFERENCE_TOTAL_BYTES // (1024 * 1024)} MB"
            )
        try:
            with Image.open(io.BytesIO(decoded), formats=PIL_ALLOWED_FORMATS) as image:
                image_format = image.format
                if image.width * image.height > MAX_REFERENCE_PIXELS:
                    raise ReferenceImageError("参考图片像素尺寸过大")
                image.verify()
        except ReferenceImageError:
            raise
        except Exception as exc:
            raise ReferenceImageError("参考图片不是有效或受支持的图片文件") from exc
        if image_format not in REFERENCE_FORMATS:
            raise ReferenceImageError("参考图片格式不受支持")
        mime_type, extension = REFERENCE_FORMATS[image_format]
        filename = (
            f"ref_{session_id}_{message_index}_{i}_{uuid.uuid4().hex[:10]}{extension}"
        )
        contents.append(types.Part.from_bytes(data=decoded, mime_type=mime_type))
        decoded_images.append({"filename": filename, "data": decoded})
    return contents, decoded_images


def _save_reference_images(decoded_images):
    filenames = []
    try:
        for item in decoded_images:
            path = os.path.join(IMAGES_DIR, item["filename"])
            with open(path, "xb") as f:
                f.write(item["data"])
            _harden_private_path(path, 0o600)
            filenames.append(item["filename"])
        return filenames
    except Exception:
        for filename in filenames:
            try:
                os.remove(os.path.join(IMAGES_DIR, filename))
            except OSError:
                pass
        raise


def _process_gemini_response(response, session_id):
    """处理 Gemini API 响应：提取文本、图片、缩略图和签名"""
    if response.parts is None:
        return None

    result_text = ""
    result_image = None
    result_thumbnail = None
    image_thought_signature = None
    text_thought_signature = None
    created_files = []

    try:
        for part in response.parts:
            if part.text is not None:
                result_text += part.text
                # 提取文本部分的 thought_signature
                if hasattr(part, 'thought_signature') and part.thought_signature:
                    if isinstance(part.thought_signature, bytes):
                        text_thought_signature = base64.b64encode(part.thought_signature).decode('utf-8')
                    else:
                        text_thought_signature = part.thought_signature
            elif part.inline_data is not None and result_image is None:
                image_filename = f"{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
                image_path = os.path.join(IMAGES_DIR, image_filename)
                created_files.append(image_path)

                image = part.as_image()
                image.save(image_path)
                _harden_private_path(image_path, 0o600)
                result_image = f"/static/images/{image_filename}"

                if hasattr(part, 'thought_signature') and part.thought_signature:
                    if isinstance(part.thought_signature, bytes):
                        image_thought_signature = base64.b64encode(part.thought_signature).decode('utf-8')
                    else:
                        image_thought_signature = part.thought_signature

                thumbnail_filename = f"thumb_{image_filename.replace('.png', '.jpg')}"
                result_thumbnail = create_thumbnail(image_path, thumbnail_filename)
                if result_thumbnail:
                    created_files.append(os.path.join(THUMBNAILS_DIR, thumbnail_filename))
    except Exception:
        for created_file in reversed(created_files):
            try:
                if os.path.exists(created_file):
                    os.remove(created_file)
            except OSError as cleanup_error:
                logger.warning(f"清理未完成的生成文件失败 {created_file}: {cleanup_error}")
        raise

    return {
        "text": result_text,
        "image": result_image,
        "thumbnail": result_thumbnail,
        "thought_signature": image_thought_signature,
        "text_thought_signature": text_thought_signature
    }


class NoGeneratedImageError(RuntimeError):
    pass


def _history_version(session_data):
    messages = session_data.get("messages", [])
    last_timestamp = messages[-1].get("timestamp") if messages else None
    return len(messages), last_timestamp


def _clear_active_chat(session_id):
    with active_chats_lock:
        active_chats.pop(session_id, None)


def _cleanup_generation_files(result, reference_filenames):
    for filename in reference_filenames:
        try:
            os.remove(os.path.join(IMAGES_DIR, os.path.basename(filename)))
        except FileNotFoundError:
            pass
        except OSError as exc:
            logger.warning(f"清理失败的参考图片 {filename}: {exc}")
    if result:
        _delete_message_files({
            "image": result.get("image"),
            "thumbnail": result.get("thumbnail"),
        })


def _resolve_generation_charge_safely(charge_id, refund):
    if not charge_id:
        return True
    try:
        success, message = resolve_generation_charge(charge_id, refund=refund)
        if not success:
            action = "退款" if refund else "提交"
            logger.error(f"生成扣费 {charge_id} {action}失败: {message}")
        return success
    except Exception as exc:
        # 清理文件和聊天状态不能因为数据库暂时不可用而被跳过。
        action = "退款" if refund else "提交"
        logger.error(f"生成扣费 {charge_id} {action}异常: {exc}", exc_info=True)
        return False


def _generation_charge_is_persisted(user_id, charge_id):
    sessions = load_sessions(user_id)
    return any(
        message.get("generation_charge_id") == charge_id
        for session_data in sessions.values()
        for message in session_data.get("messages", [])
    )


def reconcile_stale_generation_charges():
    """将崩溃进程遗留的过期预留按会话落盘结果提交或退款。"""
    resolved = 0
    for charge in get_stale_generation_charges(datetime.now().isoformat()):
        try:
            persisted = _generation_charge_is_persisted(
                charge["user_id"], charge["charge_id"]
            )
        except Exception as exc:
            # 读取会话失败时不能贸然退款，否则可能把已成功生成的账单退掉。
            logger.error(
                f"读取生成扣费 {charge['charge_id']} 的会话证据失败: {exc}",
                exc_info=True,
            )
            continue
        if _resolve_generation_charge_safely(
            charge["charge_id"], refund=not persisted
        ):
            resolved += 1
    return resolved


charge_reconciliation_lock = threading.Lock()
charge_reconciliation_next_at = 0.0


@app.before_request
def reconcile_generation_charges_before_request():
    """每个 worker 至多每分钟检查一次过期生成预留。"""
    global charge_reconciliation_next_at
    now = time.monotonic()
    if now < charge_reconciliation_next_at:
        return None
    if not charge_reconciliation_lock.acquire(blocking=False):
        return None
    try:
        charge_reconciliation_next_at = now + 60
        resolved = reconcile_stale_generation_charges()
        if resolved:
            logger.info(f"已对账 {resolved} 笔过期生成扣费")
    except Exception as exc:
        logger.error(f"生成扣费自动对账失败: {exc}", exc_info=True)
    finally:
        charge_reconciliation_lock.release()
    return None


def _handle_generation_failure(
    charge_id,
    result,
    reference_filenames,
    session_id,
    persisted_to_session,
):
    if persisted_to_session:
        # 会话已原子落盘，不能删除图片或退款；未提交账单会由对账器补交。
        _resolve_generation_charge_safely(charge_id, refund=False)
        return
    _cleanup_generation_files(result, reference_filenames)
    _clear_active_chat(session_id)
    _resolve_generation_charge_safely(charge_id, refund=True)


@app.route("/api/generate", methods=["POST"])
@login_required
@limiter.limit("20 per hour")  # 限制生成频率
def generate_image():
    """生成或修改图像"""
    user_id = session["user_id"]
    data = _get_json_data()
    error = _validate_generate_params(data)
    if error:
        return error
    session_id = data.get("session_id")
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    if not ensure_client_current():
        return jsonify({"error": "API 未配置，请联系管理员在后台设置 API Key"}), 503

    prompt = data.get("prompt", "")
    reference_images = data.get("reference_images", [])
    cost = 0
    charge_id = None
    result = None
    saved_ref_images = []
    persisted_to_session = False

    with _get_generation_lock(session_id):
        sessions = load_sessions(user_id)
        if session_id not in sessions:
            return jsonify({"error": "会话不存在"}), 404
        session_data = sessions[session_id]
        aspect_ratio = data.get("aspect_ratio", "auto")
        image_size = data.get("image_size", "2K")
        model = data.get("model") or get_default_model()
        if session_data.get("settings"):
            settings = session_data["settings"]
            aspect_ratio = settings.get("aspect_ratio", aspect_ratio)
            image_size = settings.get("image_size", image_size)
            model = settings.get("model", model)
        if (model not in MODEL_CAPABILITIES
                or image_size not in MODEL_CAPABILITIES[model]["sizes"]
                or (aspect_ratio != "auto" and aspect_ratio not in MODEL_CAPABILITIES[model]["ratios"])):
            return jsonify({"error": "该历史会话的模型设置已不再受支持，请新建对话"}), 400
        if len(reference_images) > MODEL_CAPABILITIES[model]["max_references"]:
            return jsonify({"error": f"{MODEL_CAPABILITIES[model]['name']} 最多支持 {MODEL_CAPABILITIES[model]['max_references']} 张参考图"}), 400

        expected_history_version = _history_version(session_data)
        try:
            contents, decoded_ref_images = _process_reference_images(
                reference_images,
                session_id,
                len(session_data.get("messages", [])),
            )
        except ReferenceImageError as exc:
            return jsonify({"error": str(exc)}), 400
        contents.append(prompt)

        user = get_user_by_id(user_id)
        if user is None:
            _clear_authentication_session()
            return jsonify({"error": "请先登录"}), 401
        credits_after_deduct = user["credits"]
        if not user.get("is_admin"):
            cost = get_model_pricing().get((model, image_size), DEFAULT_PRICES[image_size])
            if cost > 0:
                charge_id = uuid.uuid4().hex
                expires_at = (
                    datetime.now() + timedelta(seconds=GENERATION_CHARGE_TTL_SECONDS)
                ).isoformat()
                deducted, _, credits_after_deduct = reserve_generation_credits(
                    user_id, cost, charge_id, expires_at
                )
                if not deducted:
                    return jsonify({"error": f"点数不足，本次生成需要 {cost} 点，剩余 {credits_after_deduct} 点。请联系管理员充值。"}), 403

        try:
            chat = get_or_create_chat(
                session_id,
                aspect_ratio,
                image_size,
                model,
                user_id,
                expected_history_version,
            )
            response = chat.send_message(contents)

            with _get_maintenance_lock():
                result = _process_gemini_response(response, session_id)
                if result is None or not result.get("image"):
                    raise NoGeneratedImageError("AI 未返回图片，请调整提示词后重试")
                saved_ref_images = _save_reference_images(decoded_ref_images)
                now = datetime.now().isoformat()
                with _get_session_lock(user_id):
                    current_sessions = _load_sessions_unlocked(user_id)
                    current_session = current_sessions.get(session_id)
                    if current_session is None or get_user_by_id(user_id) is None:
                        raise RuntimeError("会话或用户已在生成期间被删除")
                    if _history_version(current_session) != expected_history_version:
                        raise RuntimeError("会话历史已在生成期间发生变化")
                    current_session["messages"].append({
                        "role": "user",
                        "content": prompt,
                        "reference_images": saved_ref_images or None,
                        "timestamp": now,
                    })
                    current_session["messages"].append({
                        "role": "assistant",
                        "content": result["text"],
                        "image": result["image"],
                        "thumbnail": result["thumbnail"],
                        "thought_signature": result["thought_signature"],
                        "text_thought_signature": result["text_thought_signature"],
                        "generation_charge_id": charge_id,
                        "timestamp": now,
                    })
                    if len(current_session["messages"]) == 2:
                        current_session["title"] = prompt[:20] + ("..." if len(prompt) > 20 else "")
                        current_session["settings"] = {
                            "aspect_ratio": aspect_ratio,
                            "image_size": image_size,
                            "model": model,
                        }
                    current_session["updated_at"] = now
                    _save_sessions_unlocked(user_id, current_sessions)
                    persisted_to_session = True
                    session_title = current_session["title"]
                    session_settings = current_session.get("settings")
                    new_history_version = _history_version(current_session)

            with active_chats_lock:
                if session_id in active_chats:
                    active_chats[session_id]["history_version"] = new_history_version
            _resolve_generation_charge_safely(charge_id, refund=False)
            return jsonify({
                "text": result["text"],
                "image": result["image"],
                "thumbnail": result["thumbnail"],
                "reference_images": saved_ref_images or None,
                "session_title": session_title,
                "settings": session_settings,
                "credits_remaining": credits_after_deduct if not user.get("is_admin") else "admin",
            })

        except NoGeneratedImageError as exc:
            _handle_generation_failure(
                charge_id, result, saved_ref_images, session_id, persisted_to_session
            )
            return jsonify({"error": str(exc), "error_code": "NO_IMAGE"}), 422
        except genai_errors.ServerError as exc:
            _handle_generation_failure(
                charge_id, result, saved_ref_images, session_id, persisted_to_session
            )
            logger.error(f"Image generation server error for user {user_id}: {exc}", exc_info=True)
            error_str = str(exc)
            if "DEADLINE_EXCEEDED" in error_str:
                return jsonify({"error": "error_timeout", "error_code": "DEADLINE_EXCEEDED"}), 503
            if "RESOURCE_EXHAUSTED" in error_str:
                return jsonify({"error": "error_quota_exceeded", "error_code": "RESOURCE_EXHAUSTED"}), 503
            if "UNAVAILABLE" in error_str:
                return jsonify({"error": "error_service_unavailable", "error_code": "UNAVAILABLE"}), 503
            return jsonify({"error": "error_server_busy", "error_code": "SERVER_ERROR"}), 503
        except genai_errors.ClientError as exc:
            _handle_generation_failure(
                charge_id, result, saved_ref_images, session_id, persisted_to_session
            )
            logger.warning(f"Image generation client error for user {user_id}: {exc}")
            error_str = str(exc)
            if "INVALID_ARGUMENT" in error_str:
                return jsonify({"error": "error_invalid_request", "error_code": "INVALID_ARGUMENT"}), 400
            if "PERMISSION_DENIED" in error_str:
                return jsonify({"error": "error_permission_denied", "error_code": "PERMISSION_DENIED"}), 403
            return jsonify({"error": "error_invalid_input", "error_code": "CLIENT_ERROR"}), 400
        except Exception as exc:
            _handle_generation_failure(
                charge_id, result, saved_ref_images, session_id, persisted_to_session
            )
            logger.error(f"Image generation failed for user {user_id}: {exc}", exc_info=True)
            return jsonify({"error": "error_generation_failed", "error_code": "GENERATION_FAILED"}), 500


def _user_can_access_media(user_id, filename, media_type):
    user = get_user_by_id(user_id)
    if user is None:
        return False
    if user.get("is_admin"):
        return True
    sessions = load_sessions(user_id)
    for session_data in sessions.values():
        for message in session_data.get("messages", []):
            if media_type == "thumbnail":
                if os.path.basename(message.get("thumbnail") or "") == filename:
                    return True
                continue
            if os.path.basename(message.get("image") or "") == filename:
                return True
            if os.path.basename(message.get("reference_image") or "") == filename:
                return True
            if any(os.path.basename(item) == filename for item in (message.get("reference_images") or [])):
                return True
    return False


def _serve_protected_media(directory, filename, media_type):
    safe_filename = secure_filename(filename)
    if not safe_filename or safe_filename != filename:
        return jsonify({"error": "Invalid file path"}), 400
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        logger.warning(f"Attempted to access invalid file type: {filename}")
        return jsonify({"error": "Invalid file type"}), 400

    file_path = os.path.join(directory, safe_filename)
    abs_file_path = os.path.abspath(file_path)
    abs_directory = os.path.abspath(directory)
    if os.path.commonpath([abs_file_path, abs_directory]) != abs_directory:
        logger.warning(f"Path traversal attempt detected: {filename}")
        return jsonify({"error": "Invalid file path"}), 400
    if not _user_can_access_media(session["user_id"], safe_filename, media_type):
        return jsonify({"error": "无权访问该图片"}), 403
    if not os.path.exists(abs_file_path):
        return jsonify({"error": "File not found"}), 404
    response = send_from_directory(directory, safe_filename)
    response.headers["Cache-Control"] = "private, max-age=3600"
    return response


@app.route("/static/images/<filename>")
@login_required
def serve_image(filename):
    """仅向图片所属用户或管理员提供原图。"""
    return _serve_protected_media(IMAGES_DIR, filename, "image")


@app.route("/static/thumbnails/<filename>")
@login_required
def serve_thumbnail(filename):
    """仅向图片所属用户或管理员提供缩略图。"""
    return _serve_protected_media(THUMBNAILS_DIR, filename, "thumbnail")


@app.route("/static/<path:filename>", endpoint="static")
def serve_public_static(filename):
    """公开前端资源，但生成图片必须经过上面的鉴权路由。"""
    normalized_filename = filename.replace("\\", "/")
    path_parts = normalized_filename.split("/")
    public_directories = {"css", "fonts", "js", "lib"}
    if (
        normalized_filename != filename
        or any(part in ("", ".", "..") for part in path_parts)
        or any(part.rstrip(" .") != part for part in path_parts)
        or not (
            path_parts[0].lower() in public_directories
            or (len(path_parts) == 1 and path_parts[0].lower() == "logo.ico")
        )
    ):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(os.path.join(app.root_path, "static"), normalized_filename)


# ========================================
# 管理员功能
# ========================================

@app.route("/admin")
@admin_required
def admin_page():
    """管理员控制台页面"""
    return render_template("admin.html")


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_get_users():
    """获取所有用户列表"""
    users = get_all_users()
    # 获取每个用户的会话数量
    for user in users:
        try:
            user_sessions = load_sessions(user["id"])
            user["session_count"] = len(user_sessions)
            user["message_count"] = sum(len(s.get("messages", [])) for s in user_sessions.values())
        except Exception as e:
            logger.warning(f"读取用户 {user['id']} 会话数据失败: {e}")
            user["session_count"] = 0
            user["message_count"] = 0
    return jsonify(users)


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    """删除用户"""
    target_user = get_user_by_id(user_id)
    if target_user is None:
        return jsonify({"error": "用户不存在"}), 404
    if target_user.get("is_admin"):
        return jsonify({"error": "不能删除管理员账号"}), 400

    user_sessions = {}
    message = "用户已删除"
    try:
        with _get_maintenance_lock():
            with _get_session_lock(user_id):
                user_sessions = _load_sessions_unlocked(user_id)
                success, message = delete_user(user_id)
                if not success:
                    return jsonify({"error": message}), 400

                # 数据库删除成功后再清理文件；失败只会留下可回收的孤儿文件。
                for session_data in user_sessions.values():
                    for msg in session_data.get("messages", []):
                        _delete_message_files(msg)
                sessions_file = get_user_sessions_file(user_id)
                if os.path.exists(sessions_file):
                    os.remove(sessions_file)
        with active_chats_lock:
            for sid in user_sessions:
                active_chats.pop(sid, None)
    except Exception as exc:
        logger.warning(f"用户 {user_id} 已删除，但清理其文件时出错: {exc}")
    return jsonify({"success": True, "message": message})


@app.route("/api/admin/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def admin_toggle_admin(user_id):
    """切换用户管理员状态"""
    success, message = toggle_admin(user_id)
    if success:
        return jsonify({"success": True, "new_role": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/admin/users/<int:user_id>/credits", methods=["POST"])
@admin_required
def admin_add_credits(user_id):
    """管理员给用户充值"""
    data = _get_json_data()
    try:
        amount = int(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "无效的数量"}), 400
        
    success, message, new_credits = update_user_credits(user_id, amount)
    if success:
        return jsonify({"success": True, "message": message, "new_credits": new_credits})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/admin/users/<int:user_id>/sessions", methods=["GET"])
@admin_required
def admin_get_user_sessions(user_id):
    """获取指定用户的所有会话列表（不含消息内容，加快加载）"""
    sessions = load_sessions(user_id)
    session_list = []
    for sid, data in sessions.items():
        session_list.append({
            "id": sid,
            "title": data.get("title", "新对话"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "message_count": len(data.get("messages", []))
        })
    session_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return jsonify(session_list)


@app.route("/api/admin/users/<int:user_id>/sessions/<session_id>", methods=["GET"])
@admin_required
def admin_get_session_detail(user_id, session_id):
    """获取指定用户的单个会话详情（含消息，点击时加载）"""
    sessions = load_sessions(user_id)
    if session_id in sessions:
        data = sessions[session_id]
        return jsonify({
            "id": session_id,
            "title": data.get("title", "新对话"),
            "messages": [{
                k: v for k, v in msg.items()
                if k not in (
                    "thought_signature", "text_thought_signature", "generation_charge_id",
                )
            } for msg in data.get("messages", [])]
        })
    return jsonify({"error": "会话不存在"}), 404


@app.route("/api/admin/cleanup", methods=["POST"])
@admin_required
def admin_cleanup_data():
    """清理历史数据"""
    data = _get_json_data()
    cutoff_date_str = data.get("cutoff_date")
    
    if not cutoff_date_str:
        return jsonify({"error": "请提供截止日期"}), 400
        
    try:
        if len(cutoff_date_str) == 10:
             cutoff_date = datetime.strptime(cutoff_date_str, "%Y-%m-%d")
        else:
             cutoff_date = datetime.fromisoformat(cutoff_date_str)
    except ValueError:
        return jsonify({"error": "日期格式无效"}), 400

    with _get_maintenance_lock():
        msg_stats = _cleanup_expired_messages(cutoff_date)
        orphan_stats = _cleanup_orphan_files()

    # 被裁剪的历史不能继续残留在当前进程的模型上下文中。
    with active_chats_lock:
        active_chats.clear()

    return jsonify({
        "success": True,
        "message": "清理完成",
        "deleted_stats": {
            "sessions": msg_stats["sessions"],
            "messages": msg_stats["messages"],
            "images": msg_stats["images"] + orphan_stats["images"],
            "orphan_images": orphan_stats["images"],
            "orphan_thumbnails": orphan_stats["thumbnails"]
        }
    })


def _cleanup_expired_messages(cutoff_date):
    """清理截止日期之前的消息和空会话"""
    deleted_sessions = 0
    deleted_messages = 0
    deleted_images = 0

    if not os.path.exists(SESSIONS_DIR):
        return {"sessions": 0, "messages": 0, "images": 0}

    for filename in os.listdir(SESSIONS_DIR):
        if not filename.endswith(".json") or not filename.startswith("user_"):
            continue

        # 提取 user_id 用于获取文件锁
        try:
            cleanup_user_id = int(filename.replace("user_", "").replace(".json", ""))
        except (ValueError, TypeError):
            continue

        filepath = os.path.join(SESSIONS_DIR, filename)
        lock = _get_session_lock(cleanup_user_id)
        try:
            with lock:
                if not os.path.exists(filepath):
                    continue
                sessions = _load_sessions_unlocked(cleanup_user_id)

                modified = False
                sessions_to_remove = []
                removed_messages = []
                local_deleted_images = 0

                for sid, session_data in sessions.items():
                    new_messages = []
                    session_modified = False

                    for msg in session_data.get("messages", []):
                        msg_time_str = msg.get("timestamp")
                        should_delete = False

                        if msg_time_str:
                            try:
                                msg_time = datetime.fromisoformat(msg_time_str)
                                if msg_time < cutoff_date:
                                    should_delete = True
                            except ValueError:
                                pass

                        if should_delete:
                            session_modified = True
                            removed_messages.append(msg)
                            if msg.get("image"):
                                local_deleted_images += 1
                            if msg.get("reference_images"):
                                local_deleted_images += len(msg["reference_images"])
                        else:
                            new_messages.append(msg)

                    if session_modified:
                        session_data["messages"] = new_messages
                        modified = True

                    # 如果会话变空了，则删除整个会话
                    if not session_data["messages"]:
                        updated_at_str = session_data.get("updated_at")
                        if updated_at_str:
                            try:
                                updated_at = datetime.fromisoformat(updated_at_str)
                                if updated_at < cutoff_date:
                                    sessions_to_remove.append(sid)
                            except ValueError:
                                pass
                        else:
                             sessions_to_remove.append(sid)

                for sid in sessions_to_remove:
                    del sessions[sid]
                    modified = True

                if modified:
                    _save_sessions_unlocked(cleanup_user_id, sessions)
                    for msg in removed_messages:
                        _delete_message_files(msg)
                    deleted_messages += len(removed_messages)
                    deleted_images += local_deleted_images
                    deleted_sessions += len(sessions_to_remove)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue

    return {"sessions": deleted_sessions, "messages": deleted_messages, "images": deleted_images}


def _cleanup_orphan_files():
    """清理不在任何会话中引用的孤儿图片和缩略图"""
    referenced_images = set()
    referenced_thumbnails = set()
    
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if not filename.endswith(".json") or not filename.startswith("user_"):
                continue
                
            filepath = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    sessions_data = json.load(f)
                
                for sid, session_data in sessions_data.items():
                    for msg in session_data.get("messages", []):
                        if msg.get("image"):
                            referenced_images.add(os.path.basename(msg["image"]))
                        if msg.get("thumbnail"):
                            referenced_thumbnails.add(os.path.basename(msg["thumbnail"]))
                        if msg.get("reference_images"):
                            for ref_img in msg["reference_images"]:
                                referenced_images.add(os.path.basename(ref_img))
            except Exception as e:
                logger.error(f"Error reading sessions file {filename}: {e}")
                continue
    
    orphan_images = 0
    orphan_thumbnails = 0
    
    if os.path.exists(IMAGES_DIR):
        for filename in os.listdir(IMAGES_DIR):
            if filename not in referenced_images:
                file_path = os.path.join(IMAGES_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        orphan_images += 1
                    except Exception as e:
                        logger.error(f"Error deleting orphan image {filename}: {e}")
    
    if os.path.exists(THUMBNAILS_DIR):
        for filename in os.listdir(THUMBNAILS_DIR):
            if filename not in referenced_thumbnails:
                file_path = os.path.join(THUMBNAILS_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        orphan_thumbnails += 1
                    except Exception as e:
                        logger.error(f"Error deleting orphan thumbnail {filename}: {e}")

    return {"images": orphan_images, "thumbnails": orphan_thumbnails}


@app.route("/api/admin/card-keys", methods=["GET"])
@admin_required
def admin_get_card_keys():
    """获取所有卡密列表"""
    keys = get_all_card_keys()
    return jsonify(keys)


@app.route("/api/admin/card-keys", methods=["POST"])
@admin_required
def admin_generate_card_keys():
    """管理员生成卡密"""
    data = _get_json_data()
    try:
        credits = int(data.get("credits", 0))
        count = int(data.get("count", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "无效的参数"}), 400
    
    success, message, keys = generate_card_keys(credits, count)
    if success:
        return jsonify({"success": True, "message": message, "keys": keys})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/admin/api-settings", methods=["GET"])
@admin_required
def admin_get_api_settings():
    """获取当前 API 设置（Key 脱敏）"""
    db_settings = get_active_api_settings()
    if db_settings:
        # API Key 脱敏：只显示前4位和后4位
        raw_key = db_settings["api_key"]
        if len(raw_key) > 8:
            masked_key = raw_key[:4] + "*" * (len(raw_key) - 8) + raw_key[-4:]
        else:
            masked_key = "****"
        return jsonify({
            "configured": True,
            "provider": db_settings["provider"],
            "api_key_masked": masked_key,
            "custom_base_url": db_settings.get("custom_base_url", ""),
            "default_model": db_settings.get("default_model", "gemini-3.1-flash-image"),
            "email_sender": db_settings.get("email_sender") or os.getenv("EMAIL_SENDER", ""),
            "email_password_configured": bool(db_settings.get("email_password") or os.getenv("EMAIL_PASSWORD")),
            "smtp_server": db_settings.get("smtp_server") or os.getenv("SMTP_SERVER", ""),
            "smtp_port": db_settings.get("smtp_port") or os.getenv("SMTP_PORT", ""),
            "updated_at": db_settings.get("updated_at")
        })

    # 检查是否有 .env fallback
    env_key = os.getenv("GEMINI_API_KEY")
    env_url = os.getenv("GEMINI_API_BASE_URL")
    if env_key:
        if len(env_key) > 8:
            masked_key = env_key[:4] + "*" * (len(env_key) - 8) + env_key[-4:]
        else:
            masked_key = "****"
        return jsonify({
            "configured": True,
            "provider": "custom" if env_url else "google_ai",
            "api_key_masked": masked_key,
            "custom_base_url": env_url or "",
            "default_model": os.getenv("DEFAULT_MODEL", "gemini-3.1-flash-image"),
            "email_sender": os.getenv("EMAIL_SENDER", ""),
            "email_password_configured": bool(os.getenv("EMAIL_PASSWORD")),
            "smtp_server": os.getenv("SMTP_SERVER", ""),
            "smtp_port": os.getenv("SMTP_PORT", ""),
            "source": "env",
            "updated_at": None
        })

    return jsonify({"configured": False})


@app.route("/api/admin/api-settings", methods=["POST"])
@admin_required
def admin_save_api_settings():
    """保存 API 设置并重建客户端"""
    data = _get_json_data()
    string_fields = (
        "provider", "api_key", "custom_base_url", "default_model",
        "email_sender", "email_password", "smtp_server",
    )
    if any(data.get(field) is not None and not isinstance(data.get(field), str) for field in string_fields):
        return jsonify({"error": "设置字段格式无效"}), 400
    provider = (data.get("provider") or "").strip()
    submitted_api_key = (data.get("api_key") or "").strip()
    custom_base_url = (data.get("custom_base_url") or "").strip() or None
    default_model = (data.get("default_model") or "gemini-3.1-flash-image").strip()
    email_sender = (data.get("email_sender") or "").strip() or None
    submitted_email_password = (data.get("email_password") or "").strip() or None
    smtp_server = (data.get("smtp_server") or "").strip() or None
    smtp_port = data.get("smtp_port")

    # 验证
    if provider not in ('google_ai', 'custom'):
        return jsonify({"error": "无效的服务商类型"}), 400
    if default_model not in ALLOWED_MODELS:
        return jsonify({"error": "无效的默认模型"}), 400
    if provider != 'custom':
        custom_base_url = None
    else:
        validation_error = _validate_custom_base_url(custom_base_url)
        if validation_error:
            return jsonify({"error": validation_error}), 400

    # 只允许在目标端点不变时复用数据库中的已保存秘密。环境变量秘密不会被
    # 后台静默复制进数据库，避免“改端点但留空密码”造成凭据转发。
    db_settings = get_active_api_settings()
    current_provider = db_settings.get("provider") if db_settings else None
    current_base_url = db_settings.get("custom_base_url") if db_settings else None
    if current_provider != 'custom':
        current_base_url = None
    if db_settings and (provider, custom_base_url) != (current_provider, current_base_url) \
            and not submitted_api_key:
        return jsonify({"error": "更换 API 服务商或端点时必须重新输入 API Key"}), 400

    api_key = submitted_api_key or (db_settings.get("api_key") if db_settings else None)
    if not api_key:
        return jsonify({"error": "保存到数据库时必须重新输入 API Key"}), 400

    current_email_sender = (
        (db_settings.get("email_sender") if db_settings else None)
        or os.getenv("EMAIL_SENDER")
    )
    current_smtp_server = (
        (db_settings.get("smtp_server") if db_settings else None)
        or os.getenv("SMTP_SERVER")
    )
    current_smtp_port = (
        (db_settings.get("smtp_port") if db_settings else None)
        or os.getenv("SMTP_PORT")
    )
    current_email_password = (
        (db_settings.get("email_password") if db_settings else None)
        or os.getenv("EMAIL_PASSWORD")
    )
    email_sender = email_sender or current_email_sender
    smtp_server = smtp_server or current_smtp_server
    if smtp_port in (None, ""):
        smtp_port = current_smtp_port
    if smtp_port is not None:
        try:
            smtp_port = int(smtp_port)
        except (TypeError, ValueError):
            return jsonify({"error": "SMTP 端口必须是整数"}), 400
        if not 1 <= smtp_port <= 65535:
            return jsonify({"error": "SMTP 端口必须在 1 到 65535 之间"}), 400

    smtp_target_changed = (
        (smtp_server or "").lower(), str(smtp_port or "")
    ) != (
        (current_smtp_server or "").lower(), str(current_smtp_port or "")
    )
    if smtp_target_changed and current_email_password and not submitted_email_password:
        return jsonify({"error": "更换 SMTP 服务器或端口时必须重新输入邮箱密码"}), 400
    email_password = submitted_email_password or (
        db_settings.get("email_password") if db_settings else None
    )

    # 保存到数据库
    success, message = save_api_settings(provider, api_key, custom_base_url, default_model, email_sender, email_password, smtp_server, smtp_port)
    if not success:
        return jsonify({"error": message}), 400

    # 重建客户端
    reload_success = reload_client()
    if not reload_success:
        return jsonify({"error": "设置已保存，但客户端重建失败，请检查配置"}), 500

    return jsonify({"success": True, "message": "API 设置已保存并生效"})


@app.route("/api/admin/model-pricing", methods=["GET"])
@admin_required
def admin_get_model_pricing():
    """返回后台价格编辑器需要的模型能力和当前价格。"""
    pricing = get_model_pricing()
    return jsonify({
        "models": [{
            "id": model_id, "name": config["name"],
            "sizes": [{"id": size, "credits": pricing.get((model_id, size), DEFAULT_PRICES[size])}
                      for size in config["sizes"]]
        } for model_id, config in MODEL_CAPABILITIES.items()]
    })


@app.route("/api/admin/model-pricing", methods=["PUT"])
@admin_required
def admin_save_model_pricing():
    """校验并保存管理员手工设置的每个模型/分辨率价格。"""
    data = _get_json_data()
    items = data.get("prices")
    if not isinstance(items, list):
        return jsonify({"error": "价格数据格式无效"}), 400
    prices = {}
    for item in items:
        model_id = item.get("model_id") if isinstance(item, dict) else None
        image_size = item.get("image_size") if isinstance(item, dict) else None
        try:
            credits = int(item.get("credits"))
        except (ValueError, TypeError, AttributeError):
            return jsonify({"error": "价格必须是非负整数"}), 400
        if model_id not in MODEL_CAPABILITIES or image_size not in MODEL_CAPABILITIES[model_id]["sizes"]:
            return jsonify({"error": "包含不支持的模型或分辨率"}), 400
        if not 0 <= credits <= 100000:
            return jsonify({"error": "价格必须在 0 到 100000 点之间"}), 400
        prices[(model_id, image_size)] = credits
    expected = {(model_id, size) for model_id, config in MODEL_CAPABILITIES.items() for size in config["sizes"]}
    if set(prices) != expected:
        return jsonify({"error": "请为所有受支持的模型分辨率填写价格"}), 400
    success, message = save_model_pricing(prices)
    return jsonify({"success": True, "message": message}) if success else (jsonify({"error": message}), 400)

@app.route("/api/redeem", methods=["POST"])
@login_required
def redeem_card_key():
    """用户使用卡密充值"""
    user_id = session["user_id"]
    data = _get_json_data()
    code = data.get("code", "")
    if not isinstance(code, str) or len(code) > 128:
        return jsonify({"error": "卡密格式无效"}), 400
    
    success, message, new_credits = use_card_key(code, user_id)
    if success:
        return jsonify({"success": True, "message": message, "new_credits": new_credits})
    else:
        return jsonify({"error": message}), 400


# 添加安全响应头（如果未使用Talisman）
if os.getenv('FLASK_ENV') != 'production':
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response


if __name__ == "__main__":
    # 从环境变量读取调试模式
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
