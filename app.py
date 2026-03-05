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
import logging
import time
import threading
from datetime import datetime, timedelta
from functools import wraps
from PIL import Image
import io
from filelock import FileLock
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types, errors as genai_errors
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_compress import Compress

# 配置日志（根据环境动态设置级别）
_log_level = logging.DEBUG if os.getenv('FLASK_ENV') != 'production' else logging.INFO
logging.basicConfig(level=_log_level)
logger = logging.getLogger(__name__)

# 加载 .env 文件中的环境变量（必须在导入 email_service 之前）
load_dotenv()

# 导入需要环境变量的模块
from database import create_user, verify_user, get_user_by_id, get_all_users, delete_user, toggle_admin, update_user_credits, generate_card_keys, get_all_card_keys, use_card_key, create_verification_code, verify_email_code, cleanup_expired_codes
from email_service import generate_verification_code, send_verification_email
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("请设置环境变量 SECRET_KEY 或在 .env 文件中配置")

# Session 安全配置
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # 生产环境启用HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF保护
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session过期时间

# CSRF 保护配置
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # 默认不检查，手动控制
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF token不过期
csrf = CSRFProtect(app)

# 速率限制配置
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"
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

# 配置
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("请设置环境变量 GEMINI_API_KEY 或在 .env 文件中配置")

# 自定义 API 端点（可选）
API_BASE_URL = os.getenv("GEMINI_API_BASE_URL")

# 默认模型（可通过环境变量 GEMINI_MODEL 自定义）
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-image-preview")
SESSIONS_DIR = "data/sessions"  # 改为目录，每个用户一个文件
IMAGES_DIR = "static/images"
THUMBNAILS_DIR = "static/thumbnails"

# 安全配置常量
ALLOWED_ASPECT_RATIOS = ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "3:2", "2:3"]
ALLOWED_IMAGE_SIZES = ["1K", "2K", "4K"]
ALLOWED_MODELS = {
    "gemini-3-pro-image-preview": "Nano Banana Pro",
    "gemini-3.1-flash-image-preview": "Nano Banana 2",
}
MAX_PROMPT_LENGTH = 100000  # 支持长提示词
MAX_REFERENCE_IMAGES = 14
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico'}

# 确保目录存在
os.makedirs("data", exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

# 静态文件版本号（用于缓存刷新，每次启动时更新）
APP_VERSION = str(int(time.time()))

@app.context_processor
def inject_version():
    """向所有模板注入版本号，用于静态文件缓存刷新"""
    return {"v": APP_VERSION}

# Gemini 客户端（增加超时时间以支持长提示词）
# 如果配置了自定义 API 端点，则使用自定义端点
_http_kwargs = {"timeout": 300000}  # 300秒超时（毫秒）
if API_BASE_URL:
    _http_kwargs["base_url"] = API_BASE_URL
    logger.info(f"使用自定义 API 端点: {API_BASE_URL}")
http_options = types.HttpOptions(**_http_kwargs)

client = genai.Client(
    api_key=API_KEY,
    http_options=http_options
)

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
        except Exception as e:
            logger.error(f"清理线程错误: {e}")
            time.sleep(60)  # 错误后等待60秒再重试，避免循环崩溃

cleanup_thread = threading.Thread(target=cleanup_inactive_chats, daemon=True)
cleanup_thread.start()
logger.info(f"会话自动清理已启动（闲置超时: {CHAT_IDLE_TIMEOUT}s, 检查间隔: {CHAT_CLEANUP_INTERVAL}s）")


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # 如果是 API 请求，返回 JSON 错误
            if request.path.startswith("/api/"):
                return jsonify({"error": "请先登录"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "请先登录"}), 401
            return redirect(url_for("login"))
        if not session.get("is_admin"):
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


def load_sessions(user_id):
    """加载指定用户的会话数据（带文件锁防止并发问题）"""
    sessions_file = get_user_sessions_file(user_id)
    lock = _get_session_lock(user_id)
    with lock:
        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                # JSON 文件损坏，备份并返回空数据
                logger.error(f"会话文件损坏 (user {user_id}): {e}")
                backup_file = f"{sessions_file}.corrupt.{int(time.time())}"
                try:
                    import shutil
                    shutil.copy2(sessions_file, backup_file)
                    logger.info(f"已备份损坏的会话文件到: {backup_file}")
                except Exception as backup_error:
                    logger.error(f"备份失败: {backup_error}")
                # 删除损坏的文件，让系统重新开始
                try:
                    os.remove(sessions_file)
                except Exception as remove_error:
                    logger.error(f"删除损坏文件失败: {remove_error}")
                return {}
    return {}


def save_sessions(user_id, sessions):
    """保存指定用户的会话数据（原子写入 + 文件锁，防止并发和文件损坏）"""
    sessions_file = get_user_sessions_file(user_id)
    lock = _get_session_lock(user_id)
    with lock:
        tmp_file = sessions_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, sessions_file)


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
    """安全获取请求 JSON 数据，如果不是有效 JSON 返回 None"""
    try:
        return request.get_json(silent=True) or {}
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
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果是RGBA等）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 计算缩放比例，保持宽高比
            ratio = min(max_size / img.width, max_size / img.height)
            if ratio < 1:  # 只有图片比max_size大时才缩小
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式以获得更好的压缩
            thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
            return f"/static/thumbnails/{thumbnail_filename}"
    except Exception as e:
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


def create_chat(session_id, aspect_ratio="auto", image_size="2K", model=DEFAULT_MODEL, user_id=None):
    """创建新的聊天实例，如果有历史消息则自动恢复上下文"""
    if aspect_ratio == "auto":
        image_config = types.ImageConfig(
            image_size=image_size,
        )
    else:
        image_config = types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )
    
    config = types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=image_config
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
            "last_access": time.time()
        }
    return chat


def get_or_create_chat(session_id, aspect_ratio="auto", image_size="2K", model=DEFAULT_MODEL, user_id=None):
    """获取或创建聊天实例"""
    with active_chats_lock:
        if session_id in active_chats:
            chat_data = active_chats[session_id]
            chat_data["last_access"] = time.time()  # 更新最后访问时间
            # 如果配置变了，重新创建
            if (chat_data["aspect_ratio"] != aspect_ratio or 
                chat_data["image_size"] != image_size or 
                chat_data.get("model") != model):
                pass  # 需要重建，退出锁后处理
            else:
                return chat_data["chat"]
    return create_chat(session_id, aspect_ratio, image_size, model, user_id)


@app.route("/")
def index():
    """主页"""
    user = None
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
    return render_template("index.html", user=user, default_model=DEFAULT_MODEL)


@app.route("/api/models", methods=["GET"])
@csrf.exempt
def get_models():
    """获取可用的图像生成模型列表"""
    models = [
        {"id": model_id, "name": name, "default": model_id == DEFAULT_MODEL}
        for model_id, name in ALLOWED_MODELS.items()
    ]
    return jsonify({"models": models, "default": DEFAULT_MODEL})


@app.route("/login")
def login():
    """登录页（重定向到主页，主页自带登录功能）"""
    return redirect(url_for("index"))




@app.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")  # 防止暴力破解
@csrf.exempt  # API端点不需要CSRF（使用JSON）
def api_login():
    """登录接口"""
    data = _get_json_data()
    username = data.get("username", "")
    password = data.get("password", "")
    
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
@csrf.exempt
def send_verification_code_route():
    """发送邮箱验证码"""
    data = _get_json_data()
    email = data.get("email", "").strip()
    
    if not email:
        return jsonify({"error": "error_email_required"}), 400
    
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
        return jsonify({"error": message}), 500


@app.route("/api/register", methods=["POST"])
@limiter.limit("3 per hour")  # 防止批量注册
@csrf.exempt
def api_register():
    """注册接口"""
    data = _get_json_data()
    username = data.get("username", "")
    email = data.get("email", "").strip()
    password = data.get("password", "")
    verification_code = data.get("verification_code", "").strip()
    
    # 验证邮箱和验证码
    if not email or not verification_code:
        return jsonify({"error": "请输入邮箱和验证码"}), 400
    
    # 验证验证码
    code_success, code_message = verify_email_code(email, verification_code)
    if not code_success:
        return jsonify({"error": code_message}), 400
    
    # 创建用户
    success, message, user_id = create_user(username, password, email)
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/logout", methods=["GET", "POST"])
@login_required
def api_logout():
    """登出接口"""
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/sessions", methods=["GET"])
@login_required
@csrf.exempt
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
@csrf.exempt
def create_session_route():
    """创建新会话"""
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    sessions[session_id] = {
        "title": "新对话",
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "settings": None  # 首次生成后会锁定分辨率和纵横比
    }
    save_sessions(user_id, sessions)
    return jsonify({
        "id": session_id,
        "title": "新对话",
        "created_at": now,
        "updated_at": now,
        "message_count": 0
    })


@app.route("/api/sessions/<session_id>", methods=["GET"])
@login_required
@csrf.exempt
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
        filtered_msg = {k: v for k, v in msg.items() if k not in ("thought_signature", "text_thought_signature")}
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
@csrf.exempt
def delete_session_route(session_id):
    """删除会话"""
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    if session_id in sessions:
        # 删除相关图片、缩略图和参考图片
        for msg in sessions[session_id].get("messages", []):
            _delete_message_files(msg)
        del sessions[session_id]
        save_sessions(user_id, sessions)
        # 清除活跃聊天
        with active_chats_lock:
            if session_id in active_chats:
                del active_chats[session_id]
    return jsonify({"success": True})


@app.route("/api/sessions/<session_id>/title", methods=["PUT"])
@login_required
@csrf.exempt
def update_session_title(session_id):
    """更新会话标题"""
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404
    data = _get_json_data()
    sessions[session_id]["title"] = data.get("title", "新对话")
    sessions[session_id]["updated_at"] = datetime.now().isoformat()
    save_sessions(user_id, sessions)
    return jsonify({"success": True})




def _validate_generate_params(data):
    """验证图像生成请求参数，无效时返回错误响应元组"""
    session_id = data.get("session_id")
    prompt = data.get("prompt", "")
    aspect_ratio = data.get("aspect_ratio", "auto")
    image_size = data.get("image_size", "2K")
    model = data.get("model", DEFAULT_MODEL)
    reference_images = data.get("reference_images", [])

    if not session_id or not prompt:
        return jsonify({"error": "缺少必要参数"}), 400
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        return jsonify({"error": "无效的纵横比参数"}), 400
    if image_size not in ALLOWED_IMAGE_SIZES:
        return jsonify({"error": "无效的分辨率参数"}), 400
    if model not in ALLOWED_MODELS:
        return jsonify({"error": "无效的模型参数"}), 400
    if len(prompt.strip()) == 0:
        return jsonify({"error": "提示词不能为空"}), 400
    if len(prompt) > MAX_PROMPT_LENGTH:
        return jsonify({"error": f"提示词过长，最多{MAX_PROMPT_LENGTH}字符"}), 400
    if len(reference_images) > MAX_REFERENCE_IMAGES:
        return jsonify({"error": f"参考图片过多，最多{MAX_REFERENCE_IMAGES}张"}), 400
    return None


def _process_reference_images(reference_images, session_id, message_index):
    """处理参考图片：解码 base64、保存文件、构建 API parts"""
    contents = []
    saved_ref_images = []
    for i, ref_image in enumerate(reference_images):
        if ref_image:
            image_data = ref_image
            mime_type = "image/png"
            if "," in image_data:
                header = image_data.split(",")[0]
                if header.startswith("data:") and ";" in header:
                    mime_type = header[5:header.index(";")]
                image_data = image_data.split(",")[1]
            contents.append(types.Part.from_bytes(
                data=base64.b64decode(image_data),
                mime_type=mime_type
            ))
            ref_filename = f"ref_{session_id}_{message_index}_{i}.png"
            ref_path = os.path.join(IMAGES_DIR, ref_filename)
            with open(ref_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            saved_ref_images.append(ref_filename)
    return contents, saved_ref_images


def _process_gemini_response(response, session_id):
    """处理 Gemini API 响应：提取文本、图片、缩略图和签名"""
    if response.parts is None:
        return None

    result_text = ""
    result_image = None
    result_thumbnail = None
    image_thought_signature = None
    text_thought_signature = None

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

            image = part.as_image()
            image.save(image_path)
            result_image = f"/static/images/{image_filename}"

            if hasattr(part, 'thought_signature') and part.thought_signature:
                if isinstance(part.thought_signature, bytes):
                    image_thought_signature = base64.b64encode(part.thought_signature).decode('utf-8')
                else:
                    image_thought_signature = part.thought_signature

            thumbnail_filename = f"thumb_{image_filename.replace('.png', '.jpg')}"
            result_thumbnail = create_thumbnail(image_path, thumbnail_filename)

    return {
        "text": result_text,
        "image": result_image,
        "thumbnail": result_thumbnail,
        "thought_signature": image_thought_signature,
        "text_thought_signature": text_thought_signature
    }


@app.route("/api/generate", methods=["POST"])
@login_required
@limiter.limit("20 per hour")  # 限制生成频率
@csrf.exempt
def generate_image():
    """生成或修改图像"""
    user_id = session["user_id"]
    data = _get_json_data()

    # 1. 验证输入参数
    error = _validate_generate_params(data)
    if error:
        return error

    session_id = data.get("session_id")
    if not _validate_session_id(session_id):
        return jsonify({"error": "无效的会话ID"}), 400
    prompt = data.get("prompt", "")
    aspect_ratio = data.get("aspect_ratio", "auto")
    image_size = data.get("image_size", "2K")
    model = data.get("model", DEFAULT_MODEL)
    reference_images = data.get("reference_images", [])

    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404

    # 强制使用会话锁定的设置
    if sessions[session_id].get("settings"):
        settings = sessions[session_id]["settings"]
        aspect_ratio = settings.get("aspect_ratio", aspect_ratio)
        image_size = settings.get("image_size", image_size)
        model = settings.get("model", model)

    # 预初始化变量，确保异常处理块中可以安全访问
    cost = 0
    user = None

    try:
        # 2. 检查并扣除点数（管理员免消耗）
        user = get_user_by_id(user_id)
        credits_after_deduct = user["credits"]  # 记录扣除后的点数
        if not user.get("is_admin"):
            cost_map = {"1K": 1, "2K": 2, "4K": 4}
            cost = cost_map.get(image_size, 2)

            if user["credits"] < cost:
                return jsonify({"error": f"点数不足，本次生成需要 {cost} 点，剩余 {user['credits']} 点。请联系管理员充值。"}), 403

            _, _, credits_after_deduct = update_user_credits(user_id, -cost)

        # 3. 获取或创建聊天实例
        chat = get_or_create_chat(session_id, aspect_ratio, image_size, model, user_id)

        # 4. 处理参考图片
        contents, saved_ref_images = _process_reference_images(
            reference_images, session_id, len(sessions[session_id]['messages'])
        )
        contents.append(prompt)

        # 5. 调用 Gemini API
        response = chat.send_message(contents)

        # 6. 处理 API 响应
        result = _process_gemini_response(response, session_id)
        if result is None:
            return jsonify({"error": "AI 未返回有效响应，请重试"}), 500

        # 7. 保存消息到会话
        now = datetime.now().isoformat()

        sessions[session_id]["messages"].append({
            "role": "user",
            "content": prompt,
            "reference_images": saved_ref_images if saved_ref_images else None,
            "timestamp": now
        })

        sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": result["text"],
            "image": result["image"],
            "thumbnail": result["thumbnail"] if result["image"] else None,
            "thought_signature": result["thought_signature"],
            "text_thought_signature": result["text_thought_signature"],
            "timestamp": now
        })

        # 更新会话标题（如果是第一条消息）
        if len(sessions[session_id]["messages"]) == 2:
            sessions[session_id]["title"] = prompt[:20] + ("..." if len(prompt) > 20 else "")
            sessions[session_id]["settings"] = {
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
                "model": model
            }

        sessions[session_id]["updated_at"] = now
        save_sessions(user_id, sessions)

        return jsonify({
            "text": result["text"],
            "image": result["image"],
            "thumbnail": result["thumbnail"],
            "session_title": sessions[session_id]["title"],
            "settings": sessions[session_id].get("settings"),
            "credits_remaining": credits_after_deduct if not user.get("is_admin") else "admin"
        })

    except genai_errors.ServerError as e:
        logger.error(f"Image generation server error for user {user_id}: {str(e)}", exc_info=True)
        # 退还已扣除的点数
        if cost > 0 and user and not user.get("is_admin"):
            update_user_credits(user_id, cost)
        error_str = str(e)

        if "DEADLINE_EXCEEDED" in error_str:
            return jsonify({"error": "error_timeout", "error_code": "DEADLINE_EXCEEDED"}), 503
        elif "RESOURCE_EXHAUSTED" in error_str:
            return jsonify({"error": "error_quota_exceeded", "error_code": "RESOURCE_EXHAUSTED"}), 503
        elif "UNAVAILABLE" in error_str:
            return jsonify({"error": "error_service_unavailable", "error_code": "UNAVAILABLE"}), 503
        else:
            return jsonify({"error": "error_server_busy", "error_code": "SERVER_ERROR"}), 503

    except genai_errors.ClientError as e:
        logger.warning(f"Image generation client error for user {user_id}: {str(e)}")
        # 退还已扣除的点数
        if cost > 0 and user and not user.get("is_admin"):
            update_user_credits(user_id, cost)
        error_str = str(e)

        if "INVALID_ARGUMENT" in error_str:
            return jsonify({"error": "error_invalid_request", "error_code": "INVALID_ARGUMENT"}), 400
        elif "PERMISSION_DENIED" in error_str:
            return jsonify({"error": "error_permission_denied", "error_code": "PERMISSION_DENIED"}), 403
        else:
            return jsonify({"error": "error_invalid_input", "error_code": "CLIENT_ERROR"}), 400

    except Exception as e:
        logger.error(f"Image generation failed for user {user_id}: {str(e)}", exc_info=True)
        # 退还已扣除的点数
        if cost > 0 and user and not user.get("is_admin"):
            update_user_credits(user_id, cost)

        if os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
            return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "error_generation_failed", "error_code": "GENERATION_FAILED"}), 500


@app.route("/static/images/<filename>")
def serve_image(filename):
    """提供图片文件（带路径遍历保护）"""
    # 安全处理文件名
    safe_filename = secure_filename(filename)
    
    # 验证文件扩展名
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        logger.warning(f"Attempted to access invalid file type: {filename}")
        return jsonify({"error": "Invalid file type"}), 400
    
    # 构建完整路径并验证
    file_path = os.path.join(IMAGES_DIR, safe_filename)
    abs_file_path = os.path.abspath(file_path)
    abs_images_dir = os.path.abspath(IMAGES_DIR)
    
    # 防止路径遍历攻击
    if not abs_file_path.startswith(abs_images_dir):
        logger.warning(f"Path traversal attempt detected: {filename}")
        return jsonify({"error": "Invalid file path"}), 400
    
    # 检查文件是否存在
    if not os.path.exists(abs_file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_from_directory(IMAGES_DIR, safe_filename)


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
@csrf.exempt
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
@csrf.exempt
def admin_delete_user(user_id):
    """删除用户"""
    # 删除用户会话中关联的所有图片和缩略图
    try:
        user_sessions = load_sessions(user_id)
        for sid, session_data in user_sessions.items():
            for msg in session_data.get("messages", []):
                _delete_message_files(msg)
    except Exception as e:
        logger.warning(f"清理用户 {user_id} 的图片文件时出错: {e}")
    
    # 删除用户会话文件和锁文件
    sessions_file = get_user_sessions_file(user_id)
    if os.path.exists(sessions_file):
        os.remove(sessions_file)
    lock_file = sessions_file + ".lock"
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass
    
    success, message = delete_user(user_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/admin/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
@csrf.exempt
def admin_toggle_admin(user_id):
    """切换用户管理员状态"""
    success, message = toggle_admin(user_id)
    if success:
        return jsonify({"success": True, "new_role": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/admin/users/<int:user_id>/credits", methods=["POST"])
@admin_required
@csrf.exempt
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
@csrf.exempt
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
@csrf.exempt
def admin_get_session_detail(user_id, session_id):
    """获取指定用户的单个会话详情（含消息，点击时加载）"""
    sessions = load_sessions(user_id)
    if session_id in sessions:
        data = sessions[session_id]
        return jsonify({
            "id": session_id,
            "title": data.get("title", "新对话"),
            "messages": [{k: v for k, v in msg.items() if k not in ("thought_signature", "text_thought_signature")} for msg in data.get("messages", [])]
        })
    return jsonify({"error": "会话不存在"}), 404


@app.route("/api/admin/cleanup", methods=["POST"])
@admin_required
@csrf.exempt
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

    # 第一步：清理过期消息
    msg_stats = _cleanup_expired_messages(cutoff_date)
    
    # 第二步：清理孤儿图片
    orphan_stats = _cleanup_orphan_files()

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
                with open(filepath, "r", encoding="utf-8") as f:
                    sessions = json.load(f)

                modified = False
                sessions_to_remove = []

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
                            deleted_messages += 1
                            session_modified = True
                            # 统计图片数
                            if msg.get("image"):
                                deleted_images += 1
                            if msg.get("reference_images"):
                                deleted_images += len(msg["reference_images"])
                            # 删除关联文件
                            _delete_message_files(msg)
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
                    deleted_sessions += 1
                    modified = True

                if modified:
                    # 使用原子写入，与 save_sessions 保持一致
                    tmp_file = filepath + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(sessions, f, ensure_ascii=False, indent=2)
                    os.replace(tmp_file, filepath)

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
@csrf.exempt
def admin_get_card_keys():
    """获取所有卡密列表"""
    keys = get_all_card_keys()
    return jsonify(keys)


@app.route("/api/admin/card-keys", methods=["POST"])
@admin_required
@csrf.exempt
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


@app.route("/api/redeem", methods=["POST"])
@login_required
@csrf.exempt
def redeem_card_key():
    """用户使用卡密充值"""
    user_id = session["user_id"]
    data = _get_json_data()
    code = data.get("code", "")
    
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
