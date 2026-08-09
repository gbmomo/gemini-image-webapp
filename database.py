"""
用户数据库模块
使用 SQLite 存储用户信息
"""

import sqlite3
import os
import re
import secrets
import string
import hashlib
import logging
from contextlib import contextmanager
from cryptography.fernet import Fernet, InvalidToken
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_FILE = os.getenv("DATABASE_FILE", "data/users.db")
ENCRYPTED_CREDENTIAL_PREFIX = "fernet:v1:"


class CredentialEncryptionError(RuntimeError):
    """凭据加密配置缺失、无效或无法解密。"""


def _get_credential_fernet(required=False):
    raw_key = (os.getenv("CREDENTIAL_ENCRYPTION_KEY") or "").strip()
    if not raw_key:
        if required:
            raise CredentialEncryptionError(
                "请配置 CREDENTIAL_ENCRYPTION_KEY 后再使用数据库凭据存储"
            )
        return None
    try:
        # Fernet 密钥是 32 字节 URL-safe Base64，标准文本为 43 个有效字符
        # 加一个末尾填充符“=”。部分部署面板保存环境变量时会去掉该填充符；
        # 它不包含密钥熵，因此在严格校验字符和长度后可安全恢复。
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}=?", raw_key):
            raise ValueError("invalid Fernet key encoding")
        normalized_key = raw_key + ("=" if len(raw_key) == 43 else "")
        return Fernet(normalized_key.encode("ascii"))
    except (ValueError, TypeError, UnicodeEncodeError) as exc:
        raise CredentialEncryptionError(
            "CREDENTIAL_ENCRYPTION_KEY 格式无效，必须是 Fernet.generate_key() "
            "生成的密钥（允许省略末尾的 =）"
        ) from exc


def _encrypt_credential(value):
    if value is None:
        return None
    cipher = _get_credential_fernet(required=True)
    token = cipher.encrypt(value.encode("utf-8")).decode("ascii")
    return ENCRYPTED_CREDENTIAL_PREFIX + token


def _decrypt_credential(value):
    if value is None or not value.startswith(ENCRYPTED_CREDENTIAL_PREFIX):
        return value
    cipher = _get_credential_fernet(required=True)
    token = value[len(ENCRYPTED_CREDENTIAL_PREFIX):]
    try:
        return cipher.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError) as exc:
        raise CredentialEncryptionError(
            "数据库凭据无法解密，请检查 CREDENTIAL_ENCRYPTION_KEY 是否与加密时一致"
        ) from exc


def _harden_private_path(path, mode):
    """POSIX 下移除组用户和其他用户权限；Windows 权限由部署 ACL 管理。"""
    if os.name != "posix" or not os.path.exists(path):
        return
    try:
        os.chmod(path, mode)
    except OSError as exc:
        logger.warning("无法收紧敏感路径权限: %s", exc)


def _get_busy_timeout_ms():
    try:
        return max(0, int(os.getenv("DATABASE_BUSY_TIMEOUT_MS", "5000")))
    except (TypeError, ValueError):
        return 5000


def get_db_connection():
    """获取数据库连接"""
    busy_timeout_ms = _get_busy_timeout_ms()
    conn = sqlite3.connect(DATABASE_FILE, timeout=busy_timeout_ms / 1000)
    _harden_private_path(DATABASE_FILE, 0o600)
    conn.row_factory = sqlite3.Row  # 返回字典形式的结果
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA secure_delete = ON")
    conn.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
    return conn


@contextmanager
def get_db():
    """数据库连接上下文管理器，自动处理 commit/rollback/close"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_card_keys_table(cursor, table_name="card_keys"):
    cursor.execute(f'''
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_hash TEXT UNIQUE NOT NULL,
            code_prefix TEXT,
            fast_hash TEXT,
            credits INTEGER NOT NULL,
            is_used INTEGER DEFAULT 0,
            used_by INTEGER,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (used_by) REFERENCES users(id)
        )
    ''')


def _migrate_card_keys_table(cursor):
    """将任意已知旧版卡密表升级到标准结构，并尽量保留旧卡密。"""
    table_exists = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='card_keys'"
    ).fetchone()
    if not table_exists:
        _create_card_keys_table(cursor)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fast_hash ON card_keys(fast_hash)")
        return

    column_rows = cursor.execute("PRAGMA table_info(card_keys)").fetchall()
    columns = {column["name"] for column in column_rows}
    canonical_columns = {
        "id", "code_hash", "code_prefix", "fast_hash", "credits",
        "is_used", "used_by", "used_at", "created_at",
    }
    if columns == canonical_columns:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fast_hash ON card_keys(fast_hash)")
        return

    logger.warning("检测到旧版本卡密表，正在迁移并保留可恢复的数据...")
    legacy_rows = cursor.execute("SELECT * FROM card_keys").fetchall()
    valid_user_ids = {
        row["id"] for row in cursor.execute("SELECT id FROM users").fetchall()
    }

    cursor.execute("DROP TABLE IF EXISTS card_keys_new")
    _create_card_keys_table(cursor, "card_keys_new")
    for row in legacy_rows:
        row_keys = set(row.keys())
        plain_code = row["code"] if "code" in row_keys else None
        normalized_code = plain_code.strip().upper() if plain_code else None
        code_hash = row["code_hash"] if "code_hash" in row_keys else None
        if not code_hash and normalized_code:
            code_hash = generate_password_hash(normalized_code)
        if not code_hash:
            logger.warning("跳过无法恢复的旧卡密记录 id=%s", row["id"] if "id" in row_keys else None)
            continue

        code_prefix = row["code_prefix"] if "code_prefix" in row_keys else None
        fast_hash = row["fast_hash"] if "fast_hash" in row_keys else None
        if normalized_code:
            code_prefix = code_prefix or normalized_code[:4]
            fast_hash = fast_hash or hashlib.sha256(normalized_code.encode()).hexdigest()

        used_by = row["used_by"] if "used_by" in row_keys else None
        if used_by not in valid_user_ids:
            used_by = None

        cursor.execute(
            '''INSERT INTO card_keys_new
               (id, code_hash, code_prefix, fast_hash, credits, is_used,
                used_by, used_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                row["id"] if "id" in row_keys else None,
                code_hash,
                code_prefix,
                fast_hash,
                row["credits"] if "credits" in row_keys and row["credits"] is not None else 0,
                row["is_used"] if "is_used" in row_keys and row["is_used"] is not None else 0,
                used_by,
                row["used_at"] if "used_at" in row_keys else None,
                row["created_at"] if "created_at" in row_keys else datetime.now().isoformat(),
            ),
        )

    cursor.execute("DROP TABLE card_keys")
    cursor.execute("ALTER TABLE card_keys_new RENAME TO card_keys")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fast_hash ON card_keys(fast_hash)")


def _create_model_pricing_table(cursor, table_name="model_pricing"):
    cursor.execute(f'''
        CREATE TABLE {table_name} (
            model_id TEXT NOT NULL,
            image_size TEXT NOT NULL,
            credits INTEGER NOT NULL CHECK (credits >= 0),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (model_id, image_size)
        )
    ''')


def _migrate_model_pricing_table(cursor):
    """重建旧定价表，移除会阻止新 UPSERT 的遗留 NOT NULL 列。"""
    table_exists = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='model_pricing'"
    ).fetchone()
    if not table_exists:
        _create_model_pricing_table(cursor)
        return

    column_rows = cursor.execute("PRAGMA table_info(model_pricing)").fetchall()
    columns = {column["name"] for column in column_rows}
    primary_key = {
        column["name"]: column["pk"] for column in column_rows if column["pk"]
    }
    canonical_columns = {"model_id", "image_size", "credits", "updated_at"}
    if columns == canonical_columns and primary_key == {"model_id": 1, "image_size": 2}:
        return

    legacy_rows = cursor.execute("SELECT * FROM model_pricing").fetchall()
    cursor.execute("DROP TABLE IF EXISTS model_pricing_new")
    _create_model_pricing_table(cursor, "model_pricing_new")
    for row in legacy_rows:
        row_keys = set(row.keys())
        model_id = row["model_id"] if "model_id" in row_keys else None
        image_size = row["image_size"] if "image_size" in row_keys else None
        if not image_size and "resolution" in row_keys:
            image_size = row["resolution"]
        credits = row["credits"] if "credits" in row_keys else None
        if credits is None and "price" in row_keys:
            credits = row["price"]
        if not model_id or not image_size:
            logger.warning("跳过缺少模型或分辨率的旧定价记录")
            continue
        try:
            credits = max(0, int(credits if credits is not None else 1))
        except (TypeError, ValueError):
            credits = 1
        updated_at = row["updated_at"] if "updated_at" in row_keys else None
        cursor.execute(
            '''INSERT INTO model_pricing_new (model_id, image_size, credits, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(model_id, image_size) DO UPDATE SET
                   credits=excluded.credits, updated_at=excluded.updated_at''',
            (model_id, image_size, credits, updated_at or datetime.now().isoformat()),
        )

    cursor.execute("DROP TABLE model_pricing")
    cursor.execute("ALTER TABLE model_pricing_new RENAME TO model_pricing")


def init_db():
    """初始化数据库，创建用户表"""
    database_directory = os.path.dirname(os.path.abspath(DATABASE_FILE))
    if database_directory:
        os.makedirs(database_directory, exist_ok=True)
        _harden_private_path(database_directory, 0o700)
    with get_db() as conn:
        # 启用 WAL 模式提升并发性能（数据库级别持久设置，只需设置一次）
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        # 检查表是否存在，如果存在检查是否有 is_admin 列
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # 检查是否有 is_admin 列
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'is_admin' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            
            if 'credits' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 4")
            
            if 'email' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        else:
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    credits INTEGER DEFAULT 4,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        # 生成扣费账本：先预留点数，生成成功后提交，失败或超时则退款。
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_charges (
                charge_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                credits INTEGER NOT NULL CHECK (credits > 0),
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'committed', 'refunded')),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                resolved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_generation_charges_pending
            ON generation_charges(status) WHERE status = 'pending'
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_generation_charges_expires
            ON generation_charges(expires_at) WHERE status = 'pending'
        ''')
        
        # 创建/迁移卡密表（哈希存储）
        _migrate_card_keys_table(cursor)
        
        # 创建邮箱验证码表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verification_codes'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            cursor.execute('''
                CREATE TABLE verification_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0
                )
            ''')
            cursor.execute("CREATE INDEX idx_email ON verification_codes(email)")
            cursor.execute("CREATE INDEX idx_expires_at ON verification_codes(expires_at)")

        # 创建 API 设置表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_settings'")
        table_exists = cursor.fetchone()

        if not table_exists:
            cursor.execute('''
                CREATE TABLE api_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL DEFAULT 'google_ai',
                    api_key TEXT NOT NULL,
                    custom_base_url TEXT,
                    vertex_project TEXT,
                    vertex_location TEXT,
                    default_model TEXT DEFAULT 'gemini-3.1-flash-image',
                    email_sender TEXT,
                    email_password TEXT,
                    smtp_server TEXT,
                    smtp_port INTEGER,
                    is_active INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # 检查是否需要增加新字段（数据库迁移）
            cursor.execute("PRAGMA table_info(api_settings)")
            columns = [column["name"] for column in cursor.fetchall()]
            if "default_model" not in columns:
                cursor.execute("ALTER TABLE api_settings ADD COLUMN default_model TEXT DEFAULT 'gemini-3.1-flash-image'")
            if "email_sender" not in columns:
                cursor.execute("ALTER TABLE api_settings ADD COLUMN email_sender TEXT")
            if "email_password" not in columns:
                cursor.execute("ALTER TABLE api_settings ADD COLUMN email_password TEXT")
            if "smtp_server" not in columns:
                cursor.execute("ALTER TABLE api_settings ADD COLUMN smtp_server TEXT")
            if "smtp_port" not in columns:
                cursor.execute("ALTER TABLE api_settings ADD COLUMN smtp_port INTEGER")

        # 模型定价表：价格以站内点数为单位，按「模型 + 输出分辨率」独立维护。
        _migrate_model_pricing_table(cursor)

def create_admin_user():
    """创建管理员账号（如果不存在）"""
    with get_db() as conn:
        # 串行化“检查并创建”，避免多个 worker 同时启动时争抢 admin 用户名。
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        admin = cursor.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        configured_password = os.getenv("ADMIN_PASSWORD")

        if not configured_password:
            raise ValueError("请设置环境变量 ADMIN_PASSWORD，程序不会把临时管理员密码写入日志")
        if os.getenv("FLASK_ENV") == "production":
            password_classes = sum((
                bool(re.search(r"[a-z]", configured_password)),
                bool(re.search(r"[A-Z]", configured_password)),
                bool(re.search(r"\d", configured_password)),
                bool(re.search(r"[^A-Za-z0-9]", configured_password)),
            ))
            if len(configured_password) < 12 or password_classes < 3:
                raise ValueError(
                    "生产环境 ADMIN_PASSWORD 至少需要 12 个字符并包含至少三类字符"
                )

        if admin is not None:
            cursor.execute(
                "UPDATE users SET password_hash = ?, is_admin = 1 WHERE id = ?",
                (generate_password_hash(configured_password), admin["id"]),
            )
            return

        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            ("admin", generate_password_hash(configured_password), 1),
        )
        logger.info("✅ 管理员账号创建成功: admin")


def _validate_user_fields(username, password, email=None):
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        return "用户名和密码不能为空"
    if len(username) < 3:
        return "用户名至少需要3个字符"
    if len(username) > 64:
        return "用户名最多64个字符"
    if len(password) < 6:
        return "密码至少需要6个字符"
    if len(password) > 256:
        return "密码最多256个字符"
    if not re.search(r'[a-zA-Z]', password) or not re.search(r'[0-9]', password):
        return "密码必须同时包含字母和数字"
    if email:
        if not isinstance(email, str):
            return "邮箱格式不正确"
        if len(email) > 254:
            return "邮箱格式不正确"
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.fullmatch(email_pattern, email):
            return "邮箱格式不正确"
    return None


def _user_integrity_error_message(error):
    return "邮箱已被使用" if "email" in str(error).lower() else "用户名已存在"


def create_user(username, password, email=None):
    """
    创建新用户
    返回: (success: bool, message: str, user_id: int or None)
    """
    validation_error = _validate_user_fields(username, password, email)
    if validation_error:
        return False, validation_error, None
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, is_admin, credits) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, 0, 4)
            )
            user_id = cursor.lastrowid
            return True, "注册成功", user_id
    except sqlite3.IntegrityError as e:
        return False, _user_integrity_error_message(e), None


def verify_user(username, password):
    """
    验证用户登录
    返回: (success: bool, message: str, user: dict or None)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
    
    if user is None:
        return False, "用户名或密码错误", None
    
    if check_password_hash(user["password_hash"], password):
        return True, "登录成功", {
            "id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"] == 1,
            "credits": user["credits"] if "credits" in user.keys() else 0,
            "created_at": user["created_at"]
        }
    else:
        return False, "用户名或密码错误", None


def get_user_by_id(user_id):
    """通过 ID 获取用户信息"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, is_admin, credits, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"] == 1,
            "credits": user["credits"],
            "created_at": user["created_at"]
        }
    return None


def get_all_users():
    """获取所有用户列表（管理员功能）"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, is_admin, credits, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
    
    return [{
        "id": user["id"],
        "username": user["username"],
        "is_admin": user["is_admin"] == 1,
        "credits": user["credits"],
        "created_at": user["created_at"]
    } for user in users]


def delete_user(user_id):
    """删除用户（管理员功能）"""
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        # 不能删除管理员
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user is None:
            return False, "用户不存在"
        if user["is_admin"] == 1:
            return False, "不能删除管理员账号"

        # 卡密保留使用状态，但解除外键引用，避免历史充值记录阻止删号。
        cursor.execute("UPDATE card_keys SET used_by = NULL WHERE used_by = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return True, "用户已删除"


def toggle_admin(user_id):
    """切换用户管理员状态（管理员功能）"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_admin, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user is None:
            return False, "用户不存在"
        
        # 不能修改 admin 账号的管理员状态
        if user["username"] == "admin":
            return False, "不能修改主管理员账号"
        
        new_status = 0 if user["is_admin"] == 1 else 1
        cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (new_status, user_id))
    
    return True, "管理员" if new_status == 1 else "普通用户"


def update_user_credits(user_id, amount):
    """原子更新用户点数；余额不足时拒绝扣减。"""
    with get_db() as conn:
        # 防止两个生成请求同时读到同一份旧余额后都扣款成功。
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        # 获取当前点数
        cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            return False, "用户不存在", 0
        
        current_credits = result["credits"]
        new_credits = current_credits + amount
        if new_credits < 0:
            return False, "点数不足", current_credits
            
        cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
    
    return True, "更新成功", new_credits


def reserve_generation_credits(user_id, credits, charge_id, expires_at):
    """原子扣除生成点数并创建 pending 账单。"""
    if (not isinstance(credits, int) or isinstance(credits, bool)
            or credits <= 0):
        return False, "扣费点数必须大于0", 0
    if not isinstance(charge_id, str) or not charge_id.strip():
        return False, "无效的扣费记录ID", 0
    if not isinstance(expires_at, str) or not expires_at.strip():
        return False, "无效的扣费过期时间", 0

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        existing = cursor.execute(
            "SELECT charge_id FROM generation_charges WHERE charge_id = ?",
            (charge_id,),
        ).fetchone()
        if existing is not None:
            user = cursor.execute(
                "SELECT credits FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return (
                False,
                "扣费记录已存在",
                user["credits"] if user is not None else 0,
            )

        cursor.execute(
            '''UPDATE users SET credits = credits - ?
               WHERE id = ? AND credits >= ?''',
            (credits, user_id, credits),
        )
        if cursor.rowcount != 1:
            user = cursor.execute(
                "SELECT credits FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user is None:
                return False, "用户不存在", 0
            return False, "点数不足", user["credits"]

        cursor.execute(
            '''INSERT INTO generation_charges
               (charge_id, user_id, credits, status, expires_at)
               VALUES (?, ?, ?, 'pending', ?)''',
            (charge_id, user_id, credits, expires_at),
        )
        remaining_credits = cursor.execute(
            "SELECT credits FROM users WHERE id = ?", (user_id,)
        ).fetchone()["credits"]
        return True, "点数已预留", remaining_credits


def resolve_generation_charge(charge_id, refund):
    """幂等地提交或退款一笔 pending 生成扣费。"""
    if not isinstance(charge_id, str) or not charge_id.strip():
        return False, "无效的扣费记录ID"
    if not isinstance(refund, bool):
        return False, "无效的结算类型"

    target_status = "refunded" if refund else "committed"
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        charge = cursor.execute(
            '''SELECT charge_id, user_id, credits, status
               FROM generation_charges WHERE charge_id = ?''',
            (charge_id,),
        ).fetchone()
        if charge is None:
            return False, "扣费记录不存在"
        if charge["status"] == target_status:
            return True, "扣费记录已结算"
        if charge["status"] != "pending":
            return False, f"扣费记录已{charge['status']}，不能重复结算"

        if refund:
            cursor.execute(
                "UPDATE users SET credits = credits + ? WHERE id = ?",
                (charge["credits"], charge["user_id"]),
            )
            if cursor.rowcount != 1:
                return False, "退款用户不存在"

        cursor.execute(
            '''UPDATE generation_charges
               SET status = ?, resolved_at = ?
               WHERE charge_id = ? AND status = 'pending' ''',
            (target_status, datetime.now().isoformat(), charge_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("生成扣费记录并发结算失败")
        return True, "扣费已退款" if refund else "扣费已提交"


def get_stale_generation_charges(now_iso):
    """返回截至指定时间已经过期但仍未结算的生成扣费。"""
    with get_db() as conn:
        rows = conn.execute(
            '''SELECT charge_id, user_id, credits, status,
                      created_at, expires_at, resolved_at
               FROM generation_charges
               WHERE status = 'pending' AND expires_at <= ?
               ORDER BY expires_at, charge_id''',
            (now_iso,),
        ).fetchall()
    return [dict(row) for row in rows]


def generate_card_key_code(length=16):
    """生成随机卡密码"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_card_keys(credits, count):
    """
    批量生成卡密
    返回: (success: bool, message: str, keys: list)
    注意：返回的 keys 列表包含明文卡密，只显示一次，数据库存储哈希值
    """
    if credits <= 0:
        return False, "点数必须大于0", []
    if count <= 0 or count > 100:
        return False, "数量必须在1-100之间", []
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        generated_keys = []
        for _ in range(count):
            # 生成唯一卡密码（明文）
            while True:
                code = generate_card_key_code()
                # 用 SHA256 做快速查找索引
                fast_hash = hashlib.sha256(code.encode()).hexdigest()
                # 检查是否已存在（用快速哈希检查）
                cursor.execute("SELECT id FROM card_keys WHERE fast_hash = ?", (fast_hash,))
                if cursor.fetchone() is None:
                    break
            
            # bcrypt 哈希用于安全验证
            code_hash = generate_password_hash(code)
            # 提取前缀（前4位）用于管理员识别
            code_prefix = code[:4]
            
            # 存储哈希值、快速索引和前缀
            cursor.execute(
                "INSERT INTO card_keys (code_hash, code_prefix, fast_hash, credits) VALUES (?, ?, ?, ?)",
                (code_hash, code_prefix, fast_hash, credits)
            )
            
            # 返回明文卡密给管理员（只在生成时显示）
            generated_keys.append({
                "code": code,  # 明文卡密，只在此次返回
                "code_prefix": code_prefix,
                "credits": credits
            })
    
    return True, f"成功生成 {count} 张卡密", generated_keys


def get_all_card_keys():
    """获取所有卡密列表（管理员功能）"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ck.id, ck.code_prefix, ck.credits, ck.is_used, ck.used_by, ck.used_at, ck.created_at, u.username
            FROM card_keys ck
            LEFT JOIN users u ON ck.used_by = u.id
            ORDER BY ck.created_at DESC
        ''')
        keys = cursor.fetchall()
    
    return [{
        "id": key["id"],
        "code_prefix": key["code_prefix"],  # 只返回前缀，不返回完整卡密
        "credits": key["credits"],
        "is_used": key["is_used"] == 1,
        "used_by": key["used_by"],
        "used_by_username": key["username"],
        "used_at": key["used_at"],
        "created_at": key["created_at"]
    } for key in keys]


def use_card_key(code, user_id):
    """
    使用卡密充值
    返回: (success: bool, message: str, new_credits: int)
    使用 SHA256 快速索引定位卡密，再用 bcrypt 验证，避免全表扫描
    """
    if not code or not code.strip():
        return False, "请输入卡密", 0
    
    code = code.strip().upper()
    
    # 计算快速查找哈希
    fast_hash = hashlib.sha256(code.encode()).hexdigest()
    
    with get_db() as conn:
        # 序列化“检查未使用 -> 标记使用 -> 充值”，避免同一卡密并发兑换。
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        # 用 fast_hash 精确定位（O(1) 查找，不再全表扫描）
        cursor.execute("SELECT * FROM card_keys WHERE is_used = 0 AND fast_hash = ?", (fast_hash,))
        candidate = cursor.fetchone()
        
        if candidate is None:
            # 兼容旧数据（没有 fast_hash 的卡密，回退到遍历方式）
            cursor.execute("SELECT * FROM card_keys WHERE is_used = 0 AND fast_hash IS NULL")
            old_keys = cursor.fetchall()
            for key in old_keys:
                if check_password_hash(key["code_hash"], code):
                    candidate = key
                    # 补充 fast_hash 以加速后续查找
                    cursor.execute("UPDATE card_keys SET fast_hash = ? WHERE id = ?", (fast_hash, key["id"]))
                    break
        
        if candidate is None:
            return False, "卡密不存在或已被使用", 0
        
        # 用 bcrypt 做最终安全验证
        if not check_password_hash(candidate["code_hash"], code):
            return False, "卡密不存在或已被使用", 0
        
        credits_to_add = candidate["credits"]
        
        # 标记卡密为已使用
        cursor.execute(
            "UPDATE card_keys SET is_used = 1, used_by = ?, used_at = ? WHERE id = ?",
            (user_id, datetime.now().isoformat(), candidate["id"])
        )
        
        # 给用户加点数
        cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user is None:
            raise ValueError("用户不存在")
        
        new_credits = user["credits"] + credits_to_add
        cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
    
    return True, f"充值成功！获得 {credits_to_add} 点", new_credits


def create_verification_code(email, code_hash, expires_at):
    """
    创建邮箱验证码记录
    返回: (success: bool, message: str)
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO verification_codes (email, code_hash, expires_at) VALUES (?, ?, ?)",
                (email, code_hash, expires_at)
            )
        return True, "验证码已创建"
    except Exception:
        logger.exception("创建验证码记录失败")
        return False, "验证码服务暂时不可用"


def delete_verification_code(email, code_hash):
    """删除尚未使用的指定验证码，供邮件发送失败时回滚。"""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM verification_codes WHERE email = ? AND code_hash = ? AND used = 0",
            (email, code_hash),
        )
        return cursor.rowcount > 0


def _get_latest_verification_code(cursor, email):
    return cursor.execute(
        '''SELECT * FROM verification_codes
           WHERE email = ? AND used = 0
           ORDER BY created_at DESC, id DESC
           LIMIT 1''',
        (email,),
    ).fetchone()


def _check_verification_record(record, code):
    if record is None:
        return "验证码不存在或已使用"
    try:
        expires_at = datetime.fromisoformat(record["expires_at"])
    except (TypeError, ValueError):
        return "验证码已过期，请重新获取"
    if datetime.now() > expires_at:
        return "验证码已过期，请重新获取"
    if not check_password_hash(record["code_hash"], code):
        return "验证码错误"
    return None


def verify_email_code(email, code):
    """
    验证邮箱验证码
    返回: (success: bool, message: str)
    """
    with get_db() as conn:
        # 同一验证码只能由一个并发请求完成“验证并消费”。
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        record = _get_latest_verification_code(cursor, email)
        verification_error = _check_verification_record(record, code)
        if verification_error:
            return False, verification_error

        cursor.execute(
            "UPDATE verification_codes SET used = 1 WHERE id = ? AND used = 0",
            (record["id"],),
        )
        if cursor.rowcount != 1:
            return False, "验证码不存在或已使用"
        return True, "验证成功"


def register_user_with_verification_code(username, password, email, code):
    """在一个事务中验证验证码、创建用户并消费验证码。"""
    validation_error = _validate_user_fields(username, password, email)
    if validation_error:
        return False, validation_error, None
    if not email or not code:
        return False, "请输入邮箱和验证码", None

    try:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()
            record = _get_latest_verification_code(cursor, email)
            verification_error = _check_verification_record(record, code)
            if verification_error:
                return False, verification_error, None

            cursor.execute(
                "UPDATE verification_codes SET used = 1 WHERE id = ? AND used = 0",
                (record["id"],),
            )
            if cursor.rowcount != 1:
                return False, "验证码不存在或已使用", None

            cursor.execute(
                '''INSERT INTO users
                   (username, email, password_hash, is_admin, credits)
                   VALUES (?, ?, ?, 0, 4)''',
                (username, email, generate_password_hash(password)),
            )
            return True, "注册成功", cursor.lastrowid
    except sqlite3.IntegrityError as error:
        # 上下文管理器会回滚验证码的 used 标记。
        return False, _user_integrity_error_message(error), None


def cleanup_expired_codes():
    """
    清理过期的验证码（可选，定期调用）
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM verification_codes WHERE expires_at < ?",
            (datetime.now().isoformat(),)
        )
        deleted_count = cursor.rowcount
    
    return deleted_count


def get_active_api_settings():
    """获取当前激活的 API 设置，并仅在内存中解密敏感字段。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_settings WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()

    if row:
        return {
            "id": row["id"],
            "provider": row["provider"],
            "api_key": _decrypt_credential(row["api_key"]),
            "custom_base_url": row["custom_base_url"],
            "default_model": row["default_model"] if "default_model" in row.keys() else 'gemini-3.1-flash-image',
            "email_sender": row["email_sender"] if "email_sender" in row.keys() else None,
            "email_password": _decrypt_credential(row["email_password"])
                if "email_password" in row.keys() else None,
            "smtp_server": row["smtp_server"] if "smtp_server" in row.keys() else None,
            "smtp_port": row["smtp_port"] if "smtp_port" in row.keys() else None,
            "is_active": row["is_active"] == 1,
            "updated_at": row["updated_at"]
        }
    return None


def migrate_api_settings_credentials():
    """加密当前配置并移除历史凭据副本；可安全重复执行。"""
    changed = False
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(
            '''SELECT * FROM api_settings
               ORDER BY is_active DESC, updated_at DESC, id DESC'''
        ).fetchall()
        if not rows:
            return False

        current = rows[0]
        api_key = current["api_key"]
        email_password = current["email_password"] if "email_password" in current.keys() else None
        # 即使已经加密也先解密一次，以便尽早发现部署密钥错误。
        plain_api_key = _decrypt_credential(api_key)
        plain_email_password = _decrypt_credential(email_password)
        encrypted_api_key = api_key
        encrypted_email_password = email_password
        if not api_key.startswith(ENCRYPTED_CREDENTIAL_PREFIX):
            encrypted_api_key = _encrypt_credential(plain_api_key)
            changed = True
        if email_password and not email_password.startswith(ENCRYPTED_CREDENTIAL_PREFIX):
            encrypted_email_password = _encrypt_credential(plain_email_password)
            changed = True

        conn.execute(
            '''UPDATE api_settings
               SET api_key = ?, email_password = ?, is_active = 1
               WHERE id = ?''',
            (encrypted_api_key, encrypted_email_password, current["id"]),
        )
        deleted = conn.execute(
            "DELETE FROM api_settings WHERE id <> ?", (current["id"],)
        ).rowcount
        changed = changed or deleted > 0 or current["is_active"] != 1

    if changed:
        # 截断 WAL 并重写数据库页，尽量移除旧明文残留。
        try:
            conn = get_db_connection()
            try:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.execute("VACUUM")
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.warning("凭据迁移完成，但数据库空间清理失败: %s", exc)
    return changed


def save_api_settings(provider, api_key, custom_base_url=None, default_model='gemini-3.1-flash-image', email_sender=None, email_password=None, smtp_server=None, smtp_port=None):
    """
    保存 API 设置（更新或插入）
    返回: (success: bool, message: str)
    """
    if not provider or provider not in ('google_ai', 'custom'):
        return False, "无效的服务商类型"

    if not api_key or not api_key.strip():
        return False, "API Key 不能为空"

    if provider == 'custom' and (not custom_base_url or not custom_base_url.strip()):
        return False, "自定义模式下必须填写 API 端点 URL"


    try:
        encrypted_api_key = _encrypt_credential(api_key.strip())
        encrypted_email_password = (
            _encrypt_credential(email_password.strip()) if email_password else None
        )
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()
            current = cursor.execute(
                '''SELECT id FROM api_settings
                   ORDER BY is_active DESC, updated_at DESC, id DESC LIMIT 1'''
            ).fetchone()
            values = (
                provider,
                encrypted_api_key,
                custom_base_url.strip() if custom_base_url else None,
                default_model.strip() if default_model else 'gemini-3.1-flash-image',
                email_sender.strip() if email_sender else None,
                encrypted_email_password,
                smtp_server.strip() if smtp_server else None,
                int(smtp_port) if smtp_port else None,
                datetime.now().isoformat(),
            )
            if current:
                cursor.execute(
                    '''UPDATE api_settings SET
                       provider = ?, api_key = ?, custom_base_url = ?,
                       default_model = ?, email_sender = ?, email_password = ?,
                       smtp_server = ?, smtp_port = ?, is_active = 1, updated_at = ?
                       WHERE id = ?''',
                    values + (current["id"],),
                )
                cursor.execute("DELETE FROM api_settings WHERE id <> ?", (current["id"],))
            else:
                cursor.execute(
                    '''INSERT INTO api_settings
                       (provider, api_key, custom_base_url, default_model,
                        email_sender, email_password, smtp_server, smtp_port,
                        is_active, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)''',
                    values,
                )
        return True, "API 设置已加密保存"
    except CredentialEncryptionError as exc:
        logger.error("保存 API 设置失败: %s", exc)
        return False, str(exc)
    except Exception:
        logger.exception("保存 API 设置失败")
        return False, "保存失败，请检查服务器日志"


def get_model_pricing():
    """返回已配置的所有模型分辨率价格。"""
    with get_db() as conn:
        rows = conn.execute("SELECT model_id, image_size, credits FROM model_pricing").fetchall()
    return {(row["model_id"], row["image_size"]): row["credits"] for row in rows}


def save_model_pricing(prices):
    """原子性保存价格字典，键为 (model_id, image_size)。"""
    try:
        with get_db() as conn:
            conn.executemany(
                """INSERT INTO model_pricing (model_id, image_size, credits, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(model_id, image_size) DO UPDATE SET
                       credits=excluded.credits, updated_at=excluded.updated_at""",
                [(model_id, image_size, credits, datetime.now().isoformat())
                 for (model_id, image_size), credits in prices.items()]
            )
        return True, "模型价格已保存"
    except Exception:
        logger.exception("保存模型价格失败")
        return False, "保存失败，请检查服务器日志"


# 应用启动时自动初始化数据库
init_db()
# 加密当前 API/SMTP 凭据并清除历史配置副本
migrate_api_settings_credentials()
# 创建管理员账号
create_admin_user()

