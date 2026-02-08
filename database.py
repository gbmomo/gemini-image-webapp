"""
用户数据库模块
使用 SQLite 存储用户信息
"""

import sqlite3
import os
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DATABASE_FILE = "data/users.db"


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # 返回字典形式的结果
    return conn


def init_db():
    """初始化数据库，创建用户表"""
    os.makedirs("data", exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查表是否存在，如果存在检查是否有 is_admin 列
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # 检查是否有 is_admin 列
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_admin' not in columns:
            # 添加 is_admin 列
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        
        if 'credits' not in columns:
            # 添加 credits 列，默认送4点
            cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 4")
        
        if 'email' not in columns:
            # 添加 email 列
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        
        conn.commit()
    else:
        # 创建新表，包含 is_admin、credits 和 email 列
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
        conn.commit()
    
    # 创建/迁移卡密表（哈希存储）
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='card_keys'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # 检查是否是旧版本表结构（明文存储）
        cursor.execute("PRAGMA table_info(card_keys)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'code' in columns and 'code_hash' not in columns:
            # 旧版本表，需要删除并重建（清空所有卡密）
            print("⚠️  检测到旧版本卡密表（明文存储），正在升级到安全的哈希存储...")
            cursor.execute("DROP TABLE card_keys")
            cursor.execute('''
                CREATE TABLE card_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_hash TEXT UNIQUE NOT NULL,
                    code_prefix TEXT,
                    credits INTEGER NOT NULL,
                    is_used INTEGER DEFAULT 0,
                    used_by INTEGER,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (used_by) REFERENCES users(id)
                )
            ''')
            conn.commit()
            print("✅ 卡密表已升级，所有旧卡密已清空（安全考虑）")
    else:
        # 创建新表（哈希存储）
        cursor.execute('''
            CREATE TABLE card_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_hash TEXT UNIQUE NOT NULL,
                code_prefix TEXT,
                credits INTEGER NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (used_by) REFERENCES users(id)
            )
        ''')
        conn.commit()
    
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
        # 创建索引以加速查询
        cursor.execute("CREATE INDEX idx_email ON verification_codes(email)")
        cursor.execute("CREATE INDEX idx_expires_at ON verification_codes(expires_at)")
        conn.commit()
    
    conn.close()


def create_admin_user():
    """创建管理员账号（如果不存在）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查 admin 是否已存在
    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        # 从环境变量获取管理员密码
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_password:
            # 如果未设置，生成随机密码并输出警告
            import secrets
            import string
            admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))
            print("=" * 60)
            print("⚠️  警告：未设置 ADMIN_PASSWORD 环境变量！")
            print(f"⚠️  已自动生成管理员密码: {admin_password}")
            print("⚠️  请立即保存此密码，并在首次登录后修改！")
            print("⚠️  建议：在 .env 文件中设置 ADMIN_PASSWORD=your_password")
            print("=" * 60)
        
        # 创建 admin 用户
        password_hash = generate_password_hash(admin_password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            ("admin", password_hash, 1)
        )
        conn.commit()
        print("✅ 管理员账号创建成功: admin")
    else:
        # 确保 admin 有管理员权限
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ("admin",))
        conn.commit()
    
    conn.close()


def create_user(username, password, email=None):
    """
    创建新用户
    返回: (success: bool, message: str, user_id: int or None)
    """
    if not username or not password:
        return False, "用户名和密码不能为空", None
    
    if len(username) < 3:
        return False, "用户名至少需要3个字符", None
    
    if len(password) < 6:
        return False, "密码至少需要6个字符", None
    
    # 验证邮箱格式（如果提供）
    if email:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "邮箱格式不正确", None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, is_admin, credits) VALUES (?, ?, ?, ?, ?)",
            (username, email, password_hash, 0, 4)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, "注册成功", user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        if 'email' in str(e):
            return False, "邮箱已被使用", None
        return False, "用户名已存在", None


def verify_user(username, password):
    """
    验证用户登录
    返回: (success: bool, message: str, user: dict or None)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        return False, "用户名不存在", None
    
    if check_password_hash(user["password_hash"], password):
        return True, "登录成功", {
            "id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"] == 1,
            "credits": user["credits"] if "credits" in user.keys() else 0,
            "created_at": user["created_at"]
        }
    else:
        return False, "密码错误", None


def get_user_by_id(user_id):
    """通过 ID 获取用户信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, is_admin, credits, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, is_admin, credits, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    return [{
        "id": user["id"],
        "username": user["username"],
        "is_admin": user["is_admin"] == 1,
        "credits": user["credits"],
        "created_at": user["created_at"]
    } for user in users]


def delete_user(user_id):
    """删除用户（管理员功能）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 不能删除管理员
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user and user["is_admin"] == 1:
        conn.close()
        return False, "不能删除管理员账号"
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True, "用户已删除"


def toggle_admin(user_id):
    """切换用户管理员状态（管理员功能）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_admin, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        conn.close()
        return False, "用户不存在"
    
    # 不能修改 admin 账号的管理员状态
    if user["username"] == "admin":
        conn.close()
        return False, "不能修改主管理员账号"
    
    new_status = 0 if user["is_admin"] == 1 else 1
    cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()
    
    return True, "管理员" if new_status == 1 else "普通用户"


def update_user_credits(user_id, amount):
    """更新用户点数（增加或减少）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取当前点数
    cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result is None:
        conn.close()
        return False, "用户不存在", 0
    
    current_credits = result["credits"]
    # 确保点数不为负数（仅在减少时检查，但这取决于业务逻辑，这里允许直接加减，由调用方检查是否足够）
    # 但最终更新到数据库后，理论上不应该小于0，不过这里这是update，我们假设调用前已经check了余额不足的情况
    # 如果是管理员加分，amount是正数。如果是消费，amount是负数。
    
    new_credits = current_credits + amount
    if new_credits < 0:
        new_credits = 0
        
    cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
    conn.commit()
    conn.close()
    
    return True, "更新成功", new_credits


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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    generated_keys = []
    for _ in range(count):
        # 生成唯一卡密码（明文）
        while True:
            code = generate_card_key_code()
            # 检查哈希是否已存在（理论上极低概率）
            code_hash = generate_password_hash(code)
            cursor.execute("SELECT id FROM card_keys WHERE code_hash = ?", (code_hash,))
            if cursor.fetchone() is None:
                break
        
        # 提取前缀（前4位）用于管理员识别
        code_prefix = code[:4]
        
        # 存储哈希值和前缀
        cursor.execute(
            "INSERT INTO card_keys (code_hash, code_prefix, credits) VALUES (?, ?, ?)",
            (code_hash, code_prefix, credits)
        )
        
        # 返回明文卡密给管理员（只在生成时显示）
        generated_keys.append({
            "code": code,  # 明文卡密，只在此次返回
            "code_prefix": code_prefix,
            "credits": credits
        })
    
    conn.commit()
    conn.close()
    
    return True, f"成功生成 {count} 张卡密", generated_keys


def get_all_card_keys():
    """获取所有卡密列表（管理员功能）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ck.id, ck.code_prefix, ck.credits, ck.is_used, ck.used_by, ck.used_at, ck.created_at, u.username
        FROM card_keys ck
        LEFT JOIN users u ON ck.used_by = u.id
        ORDER BY ck.created_at DESC
    ''')
    keys = cursor.fetchall()
    conn.close()
    
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
    """
    if not code or not code.strip():
        return False, "请输入卡密", 0
    
    code = code.strip().upper()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有未使用的卡密（只获取哈希值）
    cursor.execute("SELECT * FROM card_keys WHERE is_used = 0")
    unused_keys = cursor.fetchall()
    
    if not unused_keys:
        conn.close()
        return False, "卡密不存在或已被使用", 0
    
    # 遍历未使用的卡密，验证哈希
    matched_key = None
    for key in unused_keys:
        if check_password_hash(key["code_hash"], code):
            matched_key = key
            break
    
    if matched_key is None:
        conn.close()
        return False, "卡密不存在或已被使用", 0
    
    credits_to_add = matched_key["credits"]
    
    # 标记卡密为已使用
    cursor.execute(
        "UPDATE card_keys SET is_used = 1, used_by = ?, used_at = ? WHERE id = ?",
        (user_id, datetime.now().isoformat(), matched_key["id"])
    )
    
    # 给用户加点数
    cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user is None:
        conn.rollback()
        conn.close()
        return False, "用户不存在", 0
    
    new_credits = user["credits"] + credits_to_add
    cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
    
    conn.commit()
    conn.close()
    
    return True, f"充值成功！获得 {credits_to_add} 点", new_credits


def create_verification_code(email, code_hash, expires_at):
    """
    创建邮箱验证码记录
    返回: (success: bool, message: str)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO verification_codes (email, code_hash, expires_at) VALUES (?, ?, ?)",
            (email, code_hash, expires_at)
        )
        conn.commit()
        conn.close()
        return True, "验证码已创建"
    except Exception as e:
        conn.close()
        return False, f"创建验证码失败: {str(e)}"


def verify_email_code(email, code):
    """
    验证邮箱验证码
    返回: (success: bool, message: str)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取该邮箱最新的未使用验证码
    cursor.execute("""
        SELECT * FROM verification_codes 
        WHERE email = ? AND used = 0 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (email,))
    
    record = cursor.fetchone()
    
    if record is None:
        conn.close()
        return False, "验证码不存在或已使用"
    
    # 检查是否过期
    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.now() > expires_at:
        conn.close()
        return False, "验证码已过期，请重新获取"
    
    # 验证验证码
    if check_password_hash(record["code_hash"], code):
        # 标记为已使用
        cursor.execute(
            "UPDATE verification_codes SET used = 1 WHERE id = ?",
            (record["id"],)
        )
        conn.commit()
        conn.close()
        return True, "验证成功"
    else:
        conn.close()
        return False, "验证码错误"


def cleanup_expired_codes():
    """
    清理过期的验证码（可选，定期调用）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM verification_codes WHERE expires_at < ?",
        (datetime.now().isoformat(),)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count


# 应用启动时自动初始化数据库
init_db()
# 创建管理员账号
create_admin_user()

