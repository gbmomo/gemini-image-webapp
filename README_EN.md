# Private AI Image Generation Website Based on 🍌Gemini Nano Banana API

<p align="center">
  <a href="README.md">简体中文</a> | <b>English</b>
</p>

<p align="center">
  <img src="static/logo.ico" alt="Logo" width="120" height="120">
</p>

<p align="center">
  <b>One-click deployment to own your private Gemini AI image generation website</b>
</p>

<p align="center">
  🌐 <b>Live Demo:</b> <a href="https://nano.gitsay.com/" target="_blank">https://nano.gitsay.com/</a>
</p>

<p align="center">
  Just enter your Google Gemini API Key to build a fully-featured AI image generation website<br>
  Supports user registration, credit system, multi-turn conversations, image-to-image, and more
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/gbmomo/gemini-image-webapp?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/gbmomo/gemini-image-webapp?style=flat-square" alt="Forks">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0%2B-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg" alt="License">
</p>

> ⚠️ **License Notice**: This project is licensed under [CC BY-NC-SA 4.0](LICENSE). Use of this project requires compliance with the following terms:
> 
> | Term | Requirement |
> |------|-------------|
> | **Attribution (BY)** | Must credit original author [@gbmomo](https://github.com/gbmomo) and provide [link to original project](https://github.com/gbmomo/gemini-image-webapp) |
> | **NonCommercial (NC)** | ❌ **Commercial use is strictly prohibited**. Contact the author to purchase a commercial license |
> | **ShareAlike (SA)** | Modified works must be distributed under the same CC BY-NC-SA 4.0 license |
> 
> 📧 Commercial licensing contact: S@gitsay.com | QQ: 550948321 | WeChat: Goblin_MoMo

---

## 📸 Screenshots

### Login & Registration

<p align="center">
  <img src="Display pictures/EN/登录界面.png" alt="Login" width="45%">
  <img src="Display pictures/EN/注册页面.png" alt="Registration" width="45%">
</p>

### Homepage

<p align="center">
  <img src="Display pictures/EN/网站首页（未生成之前）.png" alt="Homepage" width="80%">
</p>

### AI Image Generation

<p align="center">
  <img src="Display pictures/EN/网站首页（生成图片的效果）.png" alt="Generation Result" width="80%">
</p>

### Admin Dashboard

<p align="center">
  <img src="Display pictures/EN/管理员后台首页.png" alt="Admin Dashboard" width="80%">
</p>

---

## 🎯 What is this?

**gemini-image-webapp** is a ready-to-use AI image generation website system. Built on Google Gemini's image generation model, it allows you to quickly deploy your own AI art platform.

**Who is this for:**
- 🎨 Individuals or teams who want their own private AI art website
- 💼 Entrepreneurs looking to run an AI image generation service
- 🔧 Companies needing internal AI art generation tools
- 📚 Developers learning Flask + AI API development

**Why choose this project?**
- ✅ **Zero barrier** - Just need a Gemini API Key to run
- ✅ **Full-featured** - User system, credit billing, redemption codes included
- ✅ **Ready to use** - Beautiful UI, no frontend development needed
- ✅ **Secure** - Built-in multiple security protection mechanisms
- ✅ **Easy to deploy** - Supports local development and production deployment

---

## 🌟 Features

### 🎨 Powerful AI Image Generation
| Feature | Description |
|---------|-------------|
| **Text-to-Image** | Enter text description, AI generates images |
| **Image-to-Image** | Upload reference images, AI modifies based on description |
| **Multi-turn Conversation** | AI remembers context, continuously iterates and optimizes images |
| **Multiple References** | Support uploading up to 14 reference images |
| **Model Selection** | Switch between Nano Banana Pro (professional) and Nano Banana 2 (fast & efficient) |
| **High Resolution** | Supports 1K, 2K, 4K resolutions |
| **Multiple Aspect Ratios** | 1:1, 16:9, 9:16, 4:3, 21:9 and more |
| **Multi-language Support** | Chinese/English switching, configurable default language |

### 👥 Complete User System
| Feature | Description |
|---------|-------------|
| **User Registration** | Email verification code registration to prevent abuse |
| **User Login** | Secure password authentication |
| **Credit System** | Credits consumed based on resolution, precise billing |
| **Redemption Codes** | Users can self-recharge with redemption codes |
| **Session Management** | Multi-session management, switch conversations anytime |

### 🔧 Powerful Admin Dashboard
| Feature | Description |
|---------|-------------|
| **User Management** | View, delete users, manage permissions |
| **Credit Management** | Manually recharge credits for users |
| **Code Generation** | Batch generate redemption codes |
| **Statistics** | View user usage data |
| **Data Cleanup** | Clean historical data to free space |

### 🔒 Enterprise-grade Security
- CSRF protection
- Rate limiting to prevent brute force attacks
- Password hashing for secure storage
- Session security configuration
- Path traversal attack protection
- HTTPS enforcement in production
- Sensitive data encryption

### 🛡️ Data Security Statement
**Security Notice: All data in this application (user accounts, chat history, images, etc.) is encrypted and stored in the local SQLite database in your deployment environment.**

- We do not upload any data to third-party servers
- You have complete control over your data privacy
- Sensitive information (API Key, passwords) is hashed

### 🌐 Internationalization Support
- One-click Chinese/English interface switching
- Automatic browser language preference detection
- Customizable default language configuration

---

## 🌐 Internationalization Configuration

This system supports multi-language switching (currently Chinese and English).

### Switching Default Language

The default language is configured in `static/js/i18n.js`. You can modify the `DEFAULT_LANG` variable to change the default language:

1. Open `static/js/i18n.js`
2. Find the configuration section:

```javascript
// ========================================
// Configuration - Modify default language here
// ========================================
const DEFAULT_LANG = 'zh';  // Default: 'zh' (Chinese) or 'en' (English)
```

3. Change `'zh'` to `'en'` to set English as the default language.

### Adding New Languages

If you have development capabilities, you can add new language packs in the `translations` object in `static/js/i18n.js` and add corresponding toggle buttons in `index.html`.

---

## 🚀 Quick Start (5-minute Deployment)

### Step 1: Get the Project Code

```bash
# Clone the repository
git clone https://github.com/gbmomo/gemini-image-webapp.git

# Enter project directory
cd gemini-image-webapp
```

### Step 2: Install Python Environment

Make sure Python 3.10 or higher is installed:

```bash
# Check Python version
python --version
# Output should be Python 3.10.x or higher
```

Create a virtual environment (recommended):

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key" to create a new API Key
4. Copy the generated API Key (looks like `AIzaSy...`)

> ⚠️ **Important**: Keep your API Key safe, don't share it with others!

### Step 4: Configure Environment Variables

1. Create configuration file (copy template and rename):

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

2. Open the `.env` file you just created and fill in your configuration:

```env
# ========== Required (Just fill in these three to run!) ==========

# Your Gemini API Key (obtained in Step 3)
GEMINI_API_KEY=AIzaSyYourAPIKey

# Any complex random string for session encryption
SECRET_KEY=abc123SomeComplexRandomString

# Admin password (for logging into admin account)
ADMIN_PASSWORD=YourAdminPassword

# ========== Optional Configuration ==========

# Gemini model to use (defaults to gemini-3.1-flash-image-preview, i.e. Nano Banana 2)
# Options: gemini-3.1-flash-image-preview (Nano Banana 2, fast & efficient, DEFAULT)
#          gemini-3-pro-image-preview (Nano Banana Pro, professional)
# This controls the default selected model in the UI; users can still switch in the interface
# GEMINI_MODEL=gemini-3.1-flash-image-preview

# If you need email verification for registration:
# EMAIL_SENDER=your_email@qq.com
# EMAIL_PASSWORD=email_authorization_code
# SMTP_SERVER=smtp.qq.com
# SMTP_PORT=465
```

> 💡 **Tip**: Minimum configuration only requires the first three items to run! Email configuration can be added later.

### Step 5: Start the Application

```bash
python app.py
```

You'll see the following output when started successfully:

```
 * Running on http://127.0.0.1:5000
```

### Step 6: Start Using!

1. Open browser, visit `http://127.0.0.1:5000`
2. Login with `admin` + your admin password
3. Start creating your first AI image!

🎉 **Congratulations! You've successfully deployed your own AI image generation website!**

---

## 📖 Detailed Usage Guide

### 👤 Regular User Workflow

#### 1. Register Account
- Click "Register Now"
- Enter username, email, password
- Enter verification code from email
- Complete registration (new users get 4 free credits)

#### 2. Create Conversation
- Click "+ New Chat" button on the left
- Give the conversation a name (optional)

#### 3. Choose Parameters
- **AI Model**: Nano Banana Pro (professional), Nano Banana 2 (fast & efficient)
- **Resolution**: 1K (1 credit), 2K (2 credits), 4K (4 credits)
- **Aspect Ratio**: Auto, 1:1, 16:9, 9:16, etc.

> ⚠️ Note: Model, resolution, and aspect ratio are locked after first generation, create a new conversation to change them

#### 4. Generate Images

**Text-to-Image**: Enter text description directly
```
Example: A cute corgi running under cherry blossom trees, sunny day, anime style, high definition
```

**Image-to-Image**: Upload reference image + enter description
```
Example: Change the person in the image to cat-ear girl style
```

#### 5. Iterate and Refine
- Continue sending messages after generation
- AI remembers previously generated images
- You can say "change the background to starry sky", "make colors more vibrant", etc.

#### 6. Download Images
- Click generated image to view full size
- Click "Download Image" to save locally

### 🔧 Admin Guide

Login with `admin` account, click "Admin Dashboard" in the top right to enter admin console.

#### User Management
- View all registered users
- View user sessions and message counts
- Manually recharge credits for users
- Set/revoke admin privileges
- Delete violating users

#### Redemption Code Management
- Batch generate redemption codes
- Set credits per code
- View redemption history
- Copy and save codes immediately after generation (shown only once!)

#### Data Cleanup
- Set cutoff date
- Clean historical data before specified date
- Free up server storage space

---

## 💰 Credit Consumption

| Resolution | Pixels | Credits | Use Case |
|------------|--------|---------|----------|
| **1K** | ~1024px | 🪙 1 | Quick preview, drafts |
| **2K** | ~2048px | 🪙 2 | Daily use (recommended) |
| **4K** | ~4096px | 🪙 4 | HD wallpapers, printing |

> 💡 Admin accounts are free, no credits consumed

---

## 🌐 Production Deployment (BT Panel)

If you want to deploy the website on a server for public access, we recommend using **BT Panel (宝塔面板)** for deployment — it's simple and beginner-friendly.

> 💡 BT Panel official website: [https://www.bt.cn](https://www.bt.cn). Reference tutorial: [BT Panel Python Website Deployment Tutorial](https://www.bt.cn/bbs/thread-144409-1-1.html)

### Prerequisites

1. A cloud server with **Linux** installed (Ubuntu 20.04 / CentOS 7.9+ recommended)
2. **BT Panel** installed (version 9.0+ recommended), installation commands available at [BT Panel Official Website](https://www.bt.cn/new/download.html)
3. Install **Nginx** (1.24+ recommended) in BT Panel via "Software Store"
4. A **domain name** with DNS resolved to your server IP

### Step 0: Prepare Python Environment

Before deploying the project, you need to install a Python environment and create a virtual environment in BT Panel.

#### a. Install Python Version

1. In the BT Panel left menu, click **"Website"** → **"Python Project"**
2. Click **"Environment Management"** in the top right
3. Click **"Version Management"**
4. Find **Python 3.14.3** (or any other 3.10+ version), click **"Install"**
5. Wait for the installation to complete (takes a few minutes)

<p align="center">
  <img src="Display pictures/BT/python版本安装界面.png" alt="Python Version Installation" width="80%">
</p>

#### b. Create Virtual Environment

After installing the Python version, it's recommended to create an **isolated virtual environment** for this project, to avoid dependency conflicts between different projects.

1. In the "Environment Management" page, select the installed Python version
2. Click **"Create Virtual Environment"**
3. Enter a name for the virtual environment, e.g., `gitsay_gemini_nano`
4. Click confirm to create

<p align="center">
  <img src="Display pictures/BT/创建虚拟环境界面.png" alt="Create Virtual Environment" width="80%">
</p>

> 💡 **Why use a virtual environment?**
> A virtual environment isolates this project's dependencies from the system environment, preventing package version conflicts between different projects, making them easier to manage and maintain.

### Step 1: Upload Project Code

1. Login to BT Panel, navigate to **"Files"** management
2. Navigate to `/www/wwwroot/` directory
3. Click **"Upload"** to upload the entire project folder, e.g., the path after upload:
   ```
   /www/wwwroot/gemini-image-webapp
   ```
4. You can also use SFTP tools (e.g., WinSCP, FileZilla) to upload

> 💡 You can also use `git clone` in the terminal to pull the project code directly:
> ```bash
> cd /www/wwwroot
> git clone https://github.com/gbmomo/gemini-image-webapp.git
> ```

### Step 2: Create Python Project

1. In the BT Panel left menu, click **"Website"**
2. Click the **"Python Project"** tab
3. Click **"Add Python Project"** and fill in the following:

<p align="center">
  <img src="Display pictures/BT/宝塔面板添加python项目.png" alt="BT Panel Add Python Project" width="80%">
</p>

| Setting | Value |
|---------|-------|
| **Project Name** | `gemini-image-webapp` (customize as you like) |
| **Python Environment** | Select `Python 3.10+` (click "Environment Management" on the right to install if none available) |
| **Start Method** | Select `gunicorn` |
| **Project Path** | `/www/wwwroot/gemini-image-webapp` (your uploaded project path) |
| **Start Command** | `gunicorn -w 3 -b 0.0.0.0:5000 --timeout 300 app:app` |
| **Environment Variables** | Select "Specify Variables" (see Step 3 for details) |
| **Start User** | `www` (default is fine) |
| **Install Dependencies** | Enter the path to `requirements.txt`, or leave empty and install manually |

> ⚠️ **Start command explanation**:
> - `-w 3`: Start 3 worker processes (adjust based on server CPU cores, generally `2 * CPU cores + 1`)
> - `-b 0.0.0.0:5000`: Listen on all network interfaces on port 5000
> - `--timeout 300`: 300-second timeout (AI image generation takes time, don't set too short)
> - `app:app`: Flask application entry point

### Step 3: Configure Environment Variables

When creating the project, select **"Specify Variables"** in the Environment Variables section, then add the following variables line by line (you can also modify them later in the project **"Settings"**):

<p align="center">
  <img src="Display pictures/BT/环境变量配置界面.png" alt="Environment Variables Configuration" width="80%">
</p>

```env
EMAIL_SENDER=your_email@example.com
ADMIN_PASSWORD=YourAdminPassword
SMTP_SERVER=smtp.exmail.qq.com
EMAIL_PASSWORD=YourEmailAuthCode
SMTP_PORT=465
GEMINI_API_KEY=YourGeminiAPIKey
FLASK_ENV=production
SECRET_KEY=YourRandomSecretKeyString
FLASK_DEBUG=False
```

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Your Google Gemini API Key | ✅ Required |
| `SECRET_KEY` | Random encryption string for session encryption | ✅ Required |
| `ADMIN_PASSWORD` | Admin login password | ✅ Required |
| `FLASK_ENV` | Set to `production` | ✅ Required |
| `FLASK_DEBUG` | Set to `False` | ✅ Required |
| `EMAIL_SENDER` | Sender email address | Optional (required for registration) |
| `EMAIL_PASSWORD` | Email SMTP authorization code | Optional |
| `SMTP_SERVER` | SMTP server address | Optional |
| `SMTP_PORT` | SMTP port number (usually 465) | Optional |

> ⚠️ **Note**: After configuring environment variables, you need to **restart the project** for changes to take effect.

### Step 4: Start Project and Verify

1. After configuration, click **"Start"** or **"Restart"** button
2. Check project status, confirm it shows **"Running"**
3. Check project logs, confirm no error messages

<p align="center">
  <img src="Display pictures/BT/项目运行状态.png" alt="Project Running Status" width="80%">
</p>

4. Visit `http://YourServerIP:5000` in your browser to confirm the website is accessible

> 💡 If you can't access it, check:
> - Whether port 5000 is allowed in BT Panel "Security"
> - Whether port 5000 is open in your server's security group (e.g., AWS/GCP/Alibaba Cloud)
> - Whether there are error messages in the project logs

### Step 5: Configure Domain and External Access

#### 5.1 Bind Domain

1. In the Python project list, click the project to enter **"Settings"**
2. Find the **"Domain Management"** section
3. Add your domain, e.g., `nano.gitsay.com`

<p align="center">
  <img src="Display pictures/BT/域名绑定界面.png" alt="Domain Binding" width="80%">
</p>

#### 5.2 Enable External Mapping

1. In the project settings, find the **"External Mapping"** option
2. Click **"Enable External Mapping"** and fill in the following:

<p align="center">
  <img src="Display pictures/BT/外网映射配置.png" alt="External Mapping Configuration" width="80%">
</p>

| Setting | Value |
|---------|-------|
| **Proxy Route** | `/` |
| **Proxy Port** | `5000` |

3. Click save, BT Panel will automatically create an Nginx reverse proxy website

### Step 6: Configure SSL Certificate (HTTPS)

1. In the BT Panel left menu, click **"Website"**
2. Find the website created by the mapping, click **"Settings"**
3. Click the **"SSL"** tab on the left
4. Choose one of the following methods to apply for a certificate:
   - **Let's Encrypt**: Free certificate, click "Apply" to auto-issue
   - **BT Certificate**: Free certificate provided by BT Panel
   - **Other Certificate**: If you already have a certificate, paste the PEM-format certificate and key

<p align="center">
  <img src="Display pictures/BT/SSL证书申请.png" alt="SSL Certificate Application" width="80%">
</p>

5. After certificate is issued, enable **"Force HTTPS"**

### Step 7: Optimize Nginx Configuration (Recommended)

After the website is created, you can optimize the Nginx configuration via **"Settings" → "Configuration File"** to better support the AI image generation service.

Here's a recommended configuration reference that you can modify according to your needs:

```nginx
server
{
    listen 80;
    listen 443 ssl;
    listen 443 quic;
    http2 on;
    server_name yourdomain.com;
    index index.html index.htm default.htm default.html;
    root /www/wwwroot/gemini-image-webapp;

    #SSL-START SSL Configuration
    ssl_certificate    /www/server/panel/vhost/cert/YourSiteName/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/YourSiteName/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:!MD5:!3DES;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    error_page 497  https://$host$request_uri;
    #SSL-END

    # --- Security Enhancement Headers ---
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # --- Upload Size Limit (Max 50MB) ---
    client_max_body_size 50M;

    # --- Force HTTP to HTTPS Redirect ---
    if ($scheme = http) {
        return 301 https://$host$request_uri;
    }

    # Block access to sensitive files
    location ~* (\.env.*|\.git|\.htaccess|\.user\.ini|\.DS_Store|README\.md|requirements\.txt|\.py$)
    {
        return 404;
    }

    # --- Health Check Endpoint ---
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }

    # --- Reverse Proxy to Python Application ---
    location / {
        proxy_pass http://127.0.0.1:5000;

        # Proxy header settings
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header REMOTE-HOST $remote_addr;

        # WebSocket support (needed for streaming output)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout settings - AI generation takes longer
        proxy_connect_timeout 180s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;
    }

    access_log  /www/wwwlogs/YourSiteName.log;
    error_log  /www/wwwlogs/YourSiteName.error.log;
}
```

> ⚠️ **Important Notes**:
> - Replace `yourdomain.com` and `YourSiteName` with your actual domain and site name
> - SSL certificate paths should match what BT Panel actually generates
> - Timeout should be set to 180 seconds or more, as AI image generation requires longer processing time

### Step 8: Final Verification

1. Visit `https://yourdomain.com` in your browser
2. Confirm HTTPS certificate is working (lock icon 🔒 in address bar)
3. Login with `admin` + your admin password
4. Try generating an image to confirm all features work

🎉 **Congratulations! You've successfully deployed the AI image generation website using BT Panel!**

### Other Deployment Methods

Besides BT Panel, you can also deploy using:

- **Gunicorn + Nginx Manual Setup**: Suitable for users with Linux server admin experience
- **Docker / Docker Compose**: Suitable for users familiar with containerization
- **1Panel**: Another open-source server management panel with similar functionality

> 💡 For detailed tutorials on other deployment methods, ask an AI assistant or search for resources.

## 📁 Project Structure

```
gemini-image-webapp/
│
├── 📄 app.py                 # Main entry point (Flask application)
├── 📄 database.py            # Database operations (users, codes, etc.)
├── 📄 email_service.py       # Email service (verification codes)
├── 📄 requirements.txt       # Python dependencies
├── 📄 .env                   # Environment configuration (create yourself)
├── 📄 .env.example           # Environment template
├── 📄 .gitignore             # Git ignore rules
│
├── 📁 data/                  # Data directory (auto-generated)
│   ├── users.db              # SQLite user database
│   └── sessions/             # User session JSON files
│
├── 📁 static/                # Static resources
│   ├── css/                  # Style files
│   ├── js/                   # JavaScript scripts
│   ├── fonts/                # Font files
│   ├── lib/                  # Third-party libraries (e.g. date picker)
│   ├── logo.ico              # Website icon
│   ├── images/               # Generated images (auto-created)
│   └── thumbnails/           # Thumbnails (auto-created)
│
└── 📁 templates/             # HTML templates
    ├── index.html            # User main page
    └── admin.html            # Admin dashboard page
```

---

## ❓ FAQ

### Q: Image generation is slow/timing out?
**A:** Gemini image generation typically takes 30-60 seconds, this is normal. If frequently timing out:
- Check if network connection is stable
- Configure `GEMINI_API_BASE_URL` to use a proxy
- Reduce number of reference images

### Q: Not receiving verification code emails?
**A:** 
- Check spam folder
- Confirm email configuration is correct (use authorization code, not login password)
- QQ Mail requires enabling SMTP service first

### Q: How to use a proxy to access Gemini API?
**A:**

**Local development**: Configure in `.env` file:
```env
GEMINI_API_BASE_URL=http://your_proxy_address:port
```

**Server deployment (BT Panel)**: In BT Panel's Python project settings, find "Environment Variables" and add:
```env
GEMINI_API_BASE_URL=http://your_proxy_address:port
```
You need to **restart the project** after adding for it to take effect.

> ⚠️ **Important: This project uses Gemini official API protocol**
> 
> The API calls in this project must follow the **Google Gemini official API protocol format**, for example:
> - `http://127.0.0.1:8045/v1beta/models`
> - `https://generativelanguage.googleapis.com/v1beta/models`
> 
> If you use a third-party API proxy service, ensure it is fully compatible with the Gemini API protocol (`/v1beta/models` endpoint format), not OpenAI API format.
> 
> Configuration example:
> ```env
> GEMINI_API_BASE_URL=http://127.0.0.1:8045
> GEMINI_API_KEY=YourAPIKey
> ```

### Q: How to disable email verification for registration?
**A:** Current version requires modifying source code. Comment out the verification code validation logic in the `api_register` function in `app.py`.

### Q: Forgot admin password?
**A:** The admin password is set via the `ADMIN_PASSWORD` environment variable:
- **Local development**: Modify the `ADMIN_PASSWORD` value in your `.env` file, then restart the application
- **Server deployment (BT Panel)**: In BT Panel's Python project settings, modify the `ADMIN_PASSWORD` environment variable value, then restart the project

---

## 🔧 API Documentation

<details>
<summary>Click to expand full API documentation</summary>

### Authentication Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/login` | POST | User login | `username`, `password` |
| `/api/register` | POST | User registration | `username`, `email`, `password`, `verification_code` |
| `/api/logout` | GET | User logout | - |
| `/api/send-verification-code` | POST | Send verification code | `email` |

### Session Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | Get session list |
| `/api/sessions` | POST | Create new session |
| `/api/sessions/<id>` | GET | Get session details |
| `/api/sessions/<id>` | DELETE | Delete session |
| `/api/sessions/<id>/title` | PUT | Update session title |

### Generation Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/generate` | POST | Generate image | `session_id`, `prompt`, `aspect_ratio`, `image_size`, `model`, `reference_images` |
| `/api/models` | GET | Get available models | - |
| `/api/redeem` | POST | Redeem code | `code` |

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/users` | GET | Get user list |
| `/api/admin/users/<id>` | DELETE | Delete user |
| `/api/admin/users/<id>/credits` | POST | Add credits |
| `/api/admin/users/<id>/toggle-admin` | POST | Toggle admin privilege |
| `/api/admin/card-keys` | GET | Get redemption code list |
| `/api/admin/card-keys` | POST | Generate redemption codes |
| `/api/admin/cleanup` | POST | Clean historical data |

</details>

---

## ⚠️ Important Notes

1. **API Key Security**
   - Never commit `.env` file to Git
   - Don't share your API Key publicly

2. **Data Backup**
   - Regularly backup `data/` directory
   - Contains user data and session records

3. **Production Environment**
   - Must use HTTPS
   - Set `FLASK_ENV=production`
   - Use Gunicorn instead of Flask development server

4. **API Quota**
   - Be aware of Google Gemini API free quota limits
   - Exceeding quota requires payment or waiting for refresh

---

## 📢 Feedback

If you have questions or suggestions, feel free to submit an [Issue](https://github.com/gbmomo/gemini-image-webapp/issues)!

---

## 📄 License

This project is open-sourced under the [CC BY-NC-SA 4.0 License](LICENSE).
Commercial use of any kind is strictly prohibited.

**For commercial use, please contact the author to purchase a commercial license.**

---

## 📞 Contact

- **Email**: S@gitsay.com
- **QQ**: 550948321
- **WeChat**: Goblin_MoMo
- **GitHub**: [@gbmomo](https://github.com/gbmomo)
