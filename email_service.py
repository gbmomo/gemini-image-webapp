"""
邮件服务模块
用于发送验证码邮件
"""

import smtplib
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from email.header import Header
from email.utils import formataddr

# 配置邮箱服务器（从环境变量读取，必须在 .env 中配置）
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

logger = logging.getLogger(__name__)


def generate_verification_code(length=6):
    """
    生成随机验证码
    Args:
        length: 验证码长度，默认6位
    Returns:
        str: 数字验证码
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def send_verification_email(recipient_email, verification_code):
    """
    发送验证码邮件
    Args:
        recipient_email: 收件人邮箱地址
        verification_code: 验证码
    Returns:
        (success: bool, message: str)
    """
    if not EMAIL_PASSWORD:
        logger.error("邮箱密码未配置")
        return False, "error_email_not_configured"
    
    try:
        # 创建邮件对象
        message = MIMEMultipart('alternative')
        message['From'] = formataddr((str(Header("码言 Nano Banana", 'utf-8')), EMAIL_SENDER))
        message['To'] = recipient_email
        message['Subject'] = "码言 Nano Banana - 注册验证码"
        
        # HTML 邮件内容
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .code-box {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px;
                    margin: 30px 0;
                    border-radius: 8px;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .info {{
                    color: #666;
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 12px;
                    margin: 20px 0;
                    color: #856404;
                    border-radius: 4px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .brand {{
                    font-weight: 600;
                    color: #667eea;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍌 码言 Nano Banana Pro</h1>
                </div>
                <div class="content">
                    <p class="info">您好！</p>
                    <p class="info">感谢您注册 <span class="brand">码言 Nano Banana Pro</span>。请使用以下验证码完成注册：</p>
                    
                    <div class="code-box">
                        {verification_code}
                    </div>
                    
                    <div class="warning">
                        ⚠️ 验证码将在 <strong>10 分钟</strong>后失效，请尽快完成注册。
                    </div>
                    
                    <p class="info">如果这不是您的操作，请忽略此邮件。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。</p>
                    <p>© 2026 码言 Nano Banana Pro. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 纯文本版本（备用）
        text_content = f"""
        码言 Nano Banana Pro - 注册验证码
        
        您好！
        
        感谢您注册码言 Nano Banana Pro。请使用以下验证码完成注册：
        
        验证码：{verification_code}
        
        验证码将在 10 分钟后失效，请尽快完成注册。
        
        如果这不是您的操作，请忽略此邮件。
        
        此邮件由系统自动发送，请勿回复。
        © 2026 码言 Nano Banana Pro. All rights reserved.
        """
        
        # 添加邮件内容
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        message.attach(part1)
        message.attach(part2)
        
        # 连接到 SMTP 服务器并发送邮件
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(message)
        
        logger.info(f"验证码邮件已发送到 {recipient_email}")
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
