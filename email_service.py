"""
邮件服务模块
用于发送验证码邮件
"""

import smtplib
import secrets
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from email.header import Header
from email.utils import formataddr

from database import get_active_api_settings

logger = logging.getLogger(__name__)


def _get_smtp_timeout():
    try:
        timeout = float(os.getenv("SMTP_TIMEOUT", "15"))
        return timeout if timeout > 0 else 15.0
    except (TypeError, ValueError):
        return 15.0


def generate_verification_code(length=6):
    """
    生成随机验证码
    Args:
        length: 验证码长度，默认6位
    Returns:
        str: 数字验证码
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def send_verification_email(recipient_email, verification_code):
    """
    发送验证码邮件
    Args:
        recipient_email: 收件人邮箱地址
        verification_code: 验证码
    Returns:
        (success: bool, message: str)
    """
    # 数据库中的每个字段都可独立配置；空字段回退到环境变量。
    db_settings = get_active_api_settings() or {}
    email_sender = db_settings.get("email_sender") or os.getenv("EMAIL_SENDER", "")
    email_password = db_settings.get("email_password") or os.getenv("EMAIL_PASSWORD", "")
    smtp_server = db_settings.get("smtp_server") or os.getenv("SMTP_SERVER", "")
    smtp_port_value = db_settings.get("smtp_port") or os.getenv("SMTP_PORT", "465")
    try:
        smtp_port = int(smtp_port_value)
    except (TypeError, ValueError):
        logger.error("SMTP 端口配置无效")
        return False, "error_email_not_configured"

    if not email_password or not email_sender or not smtp_server or not smtp_port:
        logger.error("邮箱服务信息不完整，无法发送邮件")
        return False, "error_email_not_configured"
    
    try:
        # 创建邮件对象
        message = MIMEMultipart('alternative')
        message['From'] = formataddr((str(Header("码言 Nano Banana", 'utf-8')), email_sender))
        message['To'] = recipient_email
        message['Subject'] = "码言 Nano Banana 注册验证码"
        
        # HTML 邮件内容
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:24px;background:#ffffff;color:#24292f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
    <div style="max-width:520px;margin:0 auto;border:1px solid #d0d7de;border-radius:6px;padding:28px;">
        <h1 style="margin:0 0 24px;font-size:20px;font-weight:600;">码言 Nano Banana</h1>
        <p style="margin:0 0 16px;line-height:1.6;">请使用以下验证码完成注册：</p>
        <div style="margin:20px 0;padding:16px;background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;text-align:center;font-family:Consolas,'Courier New',monospace;font-size:30px;font-weight:600;letter-spacing:6px;">{verification_code}</div>
        <p style="margin:0 0 12px;line-height:1.6;">验证码将在 10 分钟后失效，请勿向他人透露。</p>
        <p style="margin:0 0 24px;line-height:1.6;">如果这不是您的操作，请忽略此邮件。</p>
        <p style="margin:0;padding-top:16px;border-top:1px solid #d8dee4;color:#57606a;font-size:13px;line-height:1.6;">此邮件由系统自动发送，请勿回复。</p>
    </div>
</body>
</html>"""
        
        # 纯文本版本（备用）
        text_content = f"""码言 Nano Banana

请使用以下验证码完成注册：

验证码：{verification_code}

验证码将在 10 分钟后失效，请勿向他人透露。

如果这不是您的操作，请忽略此邮件。

此邮件由系统自动发送，请勿回复。"""
        
        # 添加邮件内容
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        message.attach(part1)
        message.attach(part2)
        
        # 连接到 SMTP 服务器并发送邮件
        with smtplib.SMTP_SSL(
            smtp_server, smtp_port, timeout=_get_smtp_timeout()
        ) as server:
            server.login(email_sender, email_password)
            server.send_message(message)
        
        logger.info("验证码邮件发送成功")
        return True, "success"
    
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP 认证失败，请检查邮箱账号和密码")
        return False, "error_email_auth_failed"
    except smtplib.SMTPException as e:
        logger.error(f"发送邮件失败 (SMTP): {str(e)}")
        return False, "error_email_send_failed"
    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}")
        return False, "error_email_send_failed"
