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

# Gemini model to use (defaults to gemini-3-pro-image-preview)
# Options: gemini-3-pro-image-preview (Nano Banana Pro), gemini-3.1-flash-image-preview (Nano Banana 2)
# This controls the default selected model in the UI; users can still switch in the interface
# GEMINI_MODEL=gemini-3-pro-image-preview

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

## 🌐 Production Deployment

If you want to deploy the website on a server for public access, refer to these steps:

### Method 1: 1Panel Deployment (Recommended)

#### 1. Upload Project Code
Upload project code via 1Panel file manager or SFTP, e.g., to `/python-envs/nano-banana`

#### 2. Create Runtime Environment
Go to 1Panel → "Websites" → "Runtime" → "Create Runtime", fill in:

| Setting | Value |
|---------|-------|
| **Name** | nano-banana (customize) |
| **Project Directory** | Select your uploaded project path |
| **Start Command** | `pip install -r requirements.txt && gunicorn -w 6 -b 0.0.0.0:5000 --timeout 300 app:app` |
| **Application** | Python 3.10+ |
| **Container Name** | nano-banana (customize) |

#### 3. Configure Environment Variables
Switch to "Environment Variables" tab, add the following:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Gemini API Key |
| `SECRET_KEY` | Random string for session encryption |
| `ADMIN_PASSWORD` | Admin password |
| `FLASK_DEBUG` | `False` |
| `EMAIL_SENDER` | Sender email (optional) |
| `EMAIL_PASSWORD` | Email authorization code (optional) |
| `SMTP_SERVER` | SMTP server (optional) |
| `SMTP_PORT` | SMTP port (optional) |

#### 4. Configure Port
Switch to "Ports" tab, add port mapping: `5000`

#### 5. Create Website and Configure Reverse Proxy
- Go to "Websites" → "Create Website" → "Reverse Proxy"
- Enter domain, proxy address: `http://127.0.0.1:5000`
- Apply for SSL certificate, enable HTTPS

### Other Deployment Methods

Besides 1Panel, you can also deploy using:

- **Gunicorn + Nginx**: Suitable for users with Linux server admin experience
- **Docker / Docker Compose**: Suitable for users familiar with containerization
- **BT Panel**: Similar to 1Panel

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
**A:** Configure in `.env`:
```env
GEMINI_API_BASE_URL=http://your_proxy_address:port
```

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
**A:** Delete the `data/users.db` file, restart the application and a new admin account will be created automatically.

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
