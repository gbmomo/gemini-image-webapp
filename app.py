"""
Gemini 图像生成网页应用
使用 Flask + Google Gemini API
支持多轮对话的图像生成和修改
"""

import os
import json
import uuid
import base64
import logging
from datetime import datetime, timedelta
from functools import wraps
from PIL import Image
import io
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types, errors as genai_errors
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# 配置日志
logging.basicConfig(level=logging.INFO)
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
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-image-preview")
SESSIONS_DIR = "data/sessions"  # 改为目录，每个用户一个文件
IMAGES_DIR = "static/images"
THUMBNAILS_DIR = "static/thumbnails"

# 安全配置常量
ALLOWED_ASPECT_RATIOS = ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "3:2", "2:3"]
ALLOWED_IMAGE_SIZES = ["1K", "2K", "4K"]
MAX_PROMPT_LENGTH = 100000  # 支持长提示词
MAX_REFERENCE_IMAGES = 14
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico'}

# 确保目录存在
os.makedirs("data", exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

# Gemini 客户端（增加超时时间以支持长提示词）
# 如果配置了自定义 API 端点，则使用自定义端点
http_options = types.HttpOptions(
    timeout=300000  # 300秒超时（毫秒）
)
if API_BASE_URL:
    http_options = types.HttpOptions(
        timeout=300000,
        base_url=API_BASE_URL
    )
    logger.info(f"使用自定义 API 端点: {API_BASE_URL}")

client = genai.Client(
    api_key=API_KEY,
    http_options=http_options
)

# 存储活跃的聊天会话（内存中）
active_chats = {}


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



def load_sessions(user_id):
    """加载指定用户的会话数据"""
    sessions_file = get_user_sessions_file(user_id)
    if os.path.exists(sessions_file):
        with open(sessions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_sessions(user_id, sessions):
    """保存指定用户的会话数据"""
    sessions_file = get_user_sessions_file(user_id)
    with open(sessions_file, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


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
        print(f"创建缩略图失败: {e}")
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
                parts.append(msg["content"])
            
            if parts:
                history.append(types.Content(role="user", parts=parts))
        
        elif role == "assistant":
            # 添加文本
            if msg.get("content"):
                parts.append(msg["content"])
            
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
                        parts.append(types.Part.from_bytes(
                            data=image_data, mime_type=mime_type
                        ))
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
    active_chats[session_id] = {
        "chat": chat,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "model": model
    }
    return chat


def get_or_create_chat(session_id, aspect_ratio="auto", image_size="2K", model=DEFAULT_MODEL, user_id=None):
    """获取或创建聊天实例"""
    if session_id in active_chats:
        chat_data = active_chats[session_id]
        # 如果配置变了，重新创建
        if (chat_data["aspect_ratio"] != aspect_ratio or 
            chat_data["image_size"] != image_size or 
            chat_data.get("model") != model):
            return create_chat(session_id, aspect_ratio, image_size, model, user_id)
        return chat_data["chat"]
    return create_chat(session_id, aspect_ratio, image_size, model, user_id)


@app.route("/")
def index():
    """主页"""
    user = None
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
    return render_template("index.html", user=user)


@app.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")  # 防止暴力破解
@csrf.exempt  # API端点不需要CSRF（使用JSON）
def api_login():
    """登录接口"""
    data = request.json
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
    data = request.json
    email = data.get("email", "").strip()
    
    if not email:
        return jsonify({"error": "error_email_required"}), 400
    
    # 验证邮箱格式
    import re
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
    data = request.json
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


@app.route("/api/logout")
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
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404
    session_data = sessions[session_id]
    return jsonify({
        "id": session_id,
        "settings": session_data.get("settings"),  # 包含锁定的设置
        **session_data
    })


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
@login_required
@csrf.exempt
def delete_session_route(session_id):
    """删除会话"""
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    if session_id in sessions:
        # 删除相关图片、缩略图和参考图片
        for msg in sessions[session_id].get("messages", []):
            # 删除生成的图片
            if msg.get("image"):
                image_path = os.path.join(IMAGES_DIR, os.path.basename(msg["image"]))
                if os.path.exists(image_path):
                    os.remove(image_path)
            # 删除缩略图
            if msg.get("thumbnail"):
                thumb_path = os.path.join(THUMBNAILS_DIR, os.path.basename(msg["thumbnail"]))
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            # 删除参考图片
            if msg.get("reference_images"):
                for ref_img in msg["reference_images"]:
                    ref_path = os.path.join(IMAGES_DIR, os.path.basename(ref_img))
                    if os.path.exists(ref_path):
                        os.remove(ref_path)
        del sessions[session_id]
        save_sessions(user_id, sessions)
        # 清除活跃聊天
        if session_id in active_chats:
            del active_chats[session_id]
    return jsonify({"success": True})


@app.route("/api/sessions/<session_id>/title", methods=["PUT"])
@login_required
@csrf.exempt
def update_session_title(session_id):
    """更新会话标题"""
    user_id = session["user_id"]
    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404
    data = request.json
    sessions[session_id]["title"] = data.get("title", "新对话")
    sessions[session_id]["updated_at"] = datetime.now().isoformat()
    save_sessions(user_id, sessions)
    return jsonify({"success": True})


@app.route("/api/generate", methods=["POST"])
@login_required
@limiter.limit("20 per hour")  # 限制生成频率
@csrf.exempt
def generate_image():
    """生成或修改图像"""
    user_id = session["user_id"]
    data = request.json
    session_id = data.get("session_id")
    prompt = data.get("prompt", "")
    aspect_ratio = data.get("aspect_ratio", "auto")
    image_size = data.get("image_size", "2K")
    reference_images = data.get("reference_images", [])  # 改为数组

    # 输入验证
    if not session_id or not prompt:
        return jsonify({"error": "缺少必要参数"}), 400
    
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        return jsonify({"error": "无效的纵横比参数"}), 400
    
    if image_size not in ALLOWED_IMAGE_SIZES:
        return jsonify({"error": "无效的分辨率参数"}), 400
    
    if len(prompt.strip()) == 0:
        return jsonify({"error": "提示词不能为空"}), 400
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        return jsonify({"error": f"提示词过长，最多{MAX_PROMPT_LENGTH}字符"}), 400
    
    if len(reference_images) > MAX_REFERENCE_IMAGES:
        return jsonify({"error": f"参考图片过多，最多{MAX_REFERENCE_IMAGES}张"}), 400

    sessions = load_sessions(user_id)
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404

    # 强制使用会话锁定的设置
    if sessions[session_id].get("settings"):
        settings = sessions[session_id]["settings"]
        aspect_ratio = settings.get("aspect_ratio", aspect_ratio)
        image_size = settings.get("image_size", image_size)

    try:
        # 检查点数 (管理员免消耗)
        user = get_user_by_id(user_id)
        if not user.get("is_admin"):
            cost_map = {"1K": 1, "2K": 2, "4K": 4}
            cost = cost_map.get(image_size, 2)  # 默认2点
            
            if user["credits"] < cost:
                return jsonify({"error": f"点数不足，本次生成需要 {cost} 点，剩余 {user['credits']} 点。请联系管理员充值。"}), 403
            
            # 扣除点数
            update_user_credits(user_id, -cost)

        # 获取或创建聊天实例
        chat = get_or_create_chat(session_id, aspect_ratio, image_size, DEFAULT_MODEL, user_id)

        # 构建消息内容
        contents = []
        
        # 添加所有参考图片
        saved_ref_images = []
        for i, ref_image in enumerate(reference_images):
            if ref_image:
                # 从 data:image/xxx;base64, 前缀提取 MIME 类型
                image_data = ref_image
                mime_type = "image/png"  # 默认值
                if "," in image_data:
                    header = image_data.split(",")[0]
                    # 提取真实的 MIME 类型 (格式: data:image/jpeg;base64)
                    if header.startswith("data:") and ";" in header:
                        mime_type = header[5:header.index(";")]
                    image_data = image_data.split(",")[1]
                contents.append(types.Part.from_bytes(
                    data=base64.b64decode(image_data),
                    mime_type=mime_type
                ))
                # 保存参考图片
                ref_filename = f"ref_{session_id}_{len(sessions[session_id]['messages'])}_{i}.png"
                ref_path = os.path.join(IMAGES_DIR, ref_filename)
                with open(ref_path, "wb") as f:
                    f.write(base64.b64decode(image_data))
                saved_ref_images.append(ref_filename)
        
        contents.append(prompt)

        # 发送消息
        response = chat.send_message(contents)

        # 处理响应
        result_text = ""
        result_image = None

        # 检查响应是否有效
        if response.parts is None:
            return jsonify({"error": "AI 未返回有效响应，请重试"}), 500

        result_thumbnail = None
        for part in response.parts:
            if part.text is not None:
                result_text += part.text
            elif part.inline_data is not None and result_image is None:
                # 只保存第一张图片（防止重复保存）
                image_filename = f"{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
                image_path = os.path.join(IMAGES_DIR, image_filename)
                
                image = part.as_image()
                image.save(image_path)
                result_image = f"/static/images/{image_filename}"
                
                # 创建缩略图用于预览
                thumbnail_filename = f"thumb_{image_filename.replace('.png', '.jpg')}"
                result_thumbnail = create_thumbnail(image_path, thumbnail_filename)

        # 保存消息到会话
        now = datetime.now().isoformat()
        
        # 用户消息
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": prompt,
            "reference_images": saved_ref_images if saved_ref_images else None,
            "timestamp": now
        })

        # AI响应
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": result_text,
            "image": result_image,
            "thumbnail": result_thumbnail if result_image else None,
            "timestamp": now
        })

        # 更新会话标题（如果是第一条消息）
        if len(sessions[session_id]["messages"]) == 2:
            # 用提示词的前20个字符作为标题
            sessions[session_id]["title"] = prompt[:20] + ("..." if len(prompt) > 20 else "")
            # 首次生成，锁定分辨率和纵横比设置
            sessions[session_id]["settings"] = {
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
                "model": DEFAULT_MODEL
            }

        sessions[session_id]["updated_at"] = now
        save_sessions(user_id, sessions)

        return jsonify({
            "text": result_text,
            "image": result_image,
            "session_title": sessions[session_id]["title"],
            "credits_remaining": user["credits"] - cost if not user.get("is_admin") else "admin"
        })

    except genai_errors.ServerError as e:
        # 服务器端错误（超时、过载等）
        logger.error(f"Image generation server error for user {user_id}: {str(e)}", exc_info=True)
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
        # 客户端错误（无效请求等）
        logger.warning(f"Image generation client error for user {user_id}: {str(e)}")
        error_str = str(e)
        
        if "INVALID_ARGUMENT" in error_str:
            return jsonify({"error": "error_invalid_request", "error_code": "INVALID_ARGUMENT"}), 400
        elif "PERMISSION_DENIED" in error_str:
            return jsonify({"error": "error_permission_denied", "error_code": "PERMISSION_DENIED"}), 403
        else:
            return jsonify({"error": "error_invalid_input", "error_code": "CLIENT_ERROR"}), 400
    
    except Exception as e:
        # 其他未知错误
        logger.error(f"Image generation failed for user {user_id}: {str(e)}", exc_info=True)
        
        # 返回通用错误信息（生产环境不暴露细节）
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
        sessions_file = get_user_sessions_file(user["id"])
        if os.path.exists(sessions_file):
            with open(sessions_file, "r", encoding="utf-8") as f:
                user_sessions = json.load(f)
                user["session_count"] = len(user_sessions)
                user["message_count"] = sum(len(s.get("messages", [])) for s in user_sessions.values())
        else:
            user["session_count"] = 0
            user["message_count"] = 0
    return jsonify(users)


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
@csrf.exempt
def admin_delete_user(user_id):
    """删除用户"""
    # 删除用户会话文件
    sessions_file = get_user_sessions_file(user_id)
    if os.path.exists(sessions_file):
        os.remove(sessions_file)
    
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
    data = request.json
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
    """获取指定用户的所有会话"""
    sessions_file = get_user_sessions_file(user_id)
    if os.path.exists(sessions_file):
        with open(sessions_file, "r", encoding="utf-8") as f:
            sessions = json.load(f)
            session_list = []
            for sid, data in sessions.items():
                session_list.append({
                    "id": sid,
                    "title": data.get("title", "新对话"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "messages": data.get("messages", [])
                })
            session_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return jsonify(session_list)
    return jsonify([])


@app.route("/api/admin/cleanup", methods=["POST"])
@admin_required
@csrf.exempt
def admin_cleanup_data():
    """清理历史数据"""
    data = request.json
    cutoff_date_str = data.get("cutoff_date")
    
    if not cutoff_date_str:
        return jsonify({"error": "请提供截止日期"}), 400
        
    try:
        # 解析 ISO 格式日期 (YYYY-MM-DD)
        # 如果前端只传 YYYY-MM-DD，我们把它视为当天的 00:00:00，所以比较时要注意
        if len(cutoff_date_str) == 10:
             cutoff_date = datetime.strptime(cutoff_date_str, "%Y-%m-%d")
        else:
             cutoff_date = datetime.fromisoformat(cutoff_date_str)
    except ValueError:
        return jsonify({"error": "日期格式无效"}), 400

    deleted_sessions = 0
    deleted_messages = 0
    deleted_images = 0
    
    # 遍历所有用户会话文件
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if not filename.endswith(".json") or not filename.startswith("user_"):
                continue
                
            filepath = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    sessions = json.load(f)
                
                modified = False
                sessions_to_remove = []
                
                for sid, session_data in sessions.items():
                    # 检查整个会话是否过期（如果会话没有任何消息，或者最后更新时间早于截止日期）
                    # 这里为了更细粒度，我们只清理消息
                    
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
                                pass # 无法解析时间，保留
                        
                        if should_delete:
                            deleted_messages += 1
                            session_modified = True
                            # 删除关联图片和缩略图
                            if msg.get("image"):
                                image_basename = os.path.basename(msg["image"])
                                image_path = os.path.join(IMAGES_DIR, image_basename)
                                if os.path.exists(image_path):
                                    os.remove(image_path)
                                    deleted_images += 1
                                # 删除对应缩略图
                                if msg.get("thumbnail"):
                                    thumb_basename = os.path.basename(msg["thumbnail"])
                                    thumb_path = os.path.join(THUMBNAILS_DIR, thumb_basename)
                                    if os.path.exists(thumb_path):
                                        os.remove(thumb_path)
                            
                            # 删除参考图片
                            if msg.get("reference_images"):
                                for ref_img in msg["reference_images"]:
                                    ref_path = os.path.join(IMAGES_DIR, os.path.basename(ref_img))
                                    if os.path.exists(ref_path):
                                        os.remove(ref_path)
                                        deleted_images += 1
                        else:
                            new_messages.append(msg)
                    
                    if session_modified:
                        session_data["messages"] = new_messages
                        modified = True
                        
                    # 如果会话变空了，且创建时间也很老，则删除整个会话
                    # 或者如果会话本来有消息现在没了，也删掉
                    if not session_data["messages"]:
                        # 再次检查会话本身的更新时间，以防万一
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
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(sessions, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

    # === 第二步：清理孤儿图片（不在任何会话中引用的图片） ===
    # 重新收集所有会话中引用的图片（清理后的状态）
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
    
    # 清理未被引用的图片
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
    
    # 清理未被引用的缩略图
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

    return jsonify({
        "success": True,
        "message": f"清理完成",
        "deleted_stats": {
            "sessions": deleted_sessions,
            "messages": deleted_messages,
            "images": deleted_images + orphan_images,
            "orphan_images": orphan_images,
            "orphan_thumbnails": orphan_thumbnails
        }
    })


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
    data = request.json
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
    data = request.json
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
