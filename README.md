# 基于调用🍌Gemini Nano Banana api 的私有化 AI 图片生成网站源码

<p align="center">
  <b>简体中文</b> | <a href="README_EN.md">English</a>
</p>

<p align="center">
  <img src="static/logo.ico" alt="Logo" width="120" height="120">
</p>

<p align="center">
  <b>一键部署，拥有属于自己的 Gemini AI 图片生成网站</b>
</p>

<p align="center">
  🌐 <b>在线演示：</b> <a href="https://nano.gitsay.com/" target="_blank">https://nano.gitsay.com/</a>
</p>

<p align="center">
  只需填入 Google Gemini API Key，即可搭建一个功能完整的 AI 图片生成网站源码<br>
  支持用户注册、点数系统、多轮对话、图生图等丰富功能
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/gbmomo/gemini-image-webapp?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/gbmomo/gemini-image-webapp?style=flat-square" alt="Forks">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0%2B-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg" alt="License">
</p>

> ⚠️ **许可证声明**：本项目采用 [CC BY-NC-SA 4.0](LICENSE) 许可证，使用本项目需遵守以下条款：
> 
> | 条款 | 要求 |
> |------|------|
> | **署名 (BY)** | 必须注明原作者 [@gbmomo](https://github.com/gbmomo) 并提供[原项目链接](https://github.com/gbmomo/gemini-image-webapp) |
> | **非商业性 (NC)** | ❌ **严禁任何形式的商业使用**，如需商用请联系作者购买商用许可 |
> | **相同方式共享 (SA)** | 修改后的作品必须以相同的 CC BY-NC-SA 4.0 许可证发布 |
> 
> 📧 商用授权联系：S@gitsay.com | QQ: 550948321 | 微信: Goblin_MoMo

---

## 📸 效果展示

### 登录与注册

<p align="center">
  <img src="Display pictures/中文/登录界面.png" alt="登录界面" width="45%">
  <img src="Display pictures/中文/注册页面.png" alt="注册页面" width="45%">
</p>

### 网站首页

<p align="center">
  <img src="Display pictures/中文/网站首页（未生成之前）.png" alt="网站首页" width="80%">
</p>

### AI 图片生成效果

<p align="center">
  <img src="Display pictures/中文/网站首页（生成图片的效果）.png" alt="生成图片效果" width="80%">
</p>

### 管理员后台

<p align="center">
  <img src="Display pictures/中文/管理员后台首页.png" alt="管理员后台" width="80%">
</p>

---

## 🎯 这是什么？

**gemini-image-webapp** 是一个开箱即用的 AI 图片生成网站系统。基于 Google Gemini 图像生成模型，让你可以快速搭建一个属于自己的 AI 绘图平台。

**适合人群：**
- 🎨 想要拥有私有 AI 绘图网站的个人或团队
- 💼 想要运营 AI 图片生成服务的创业者
- 🔧 需要内部 AI 绘图工具的公司
- 📚 学习 Flask + AI API 开发的开发者

**为什么选择这个项目？**
- ✅ **零门槛** - 只需一个 Gemini API Key 即可运行
- ✅ **功能完整** - 用户系统、点数计费、卡密充值全都有
- ✅ **开箱即用** - 精美的 UI 界面，无需前端开发
- ✅ **安全可靠** - 内置多重安全防护机制
- ✅ **易于部署** - 支持本地开发和生产环境部署

---

## 🌟 功能亮点

### 🎨 强大的 AI 生图能力
| 功能 | 描述 |
|------|------|
| **文生图** | 输入文字描述，AI 自动生成图片 |
| **图生图** | 上传参考图片，AI 根据描述修改 |
| **多轮对话** | AI 记住上下文，持续迭代优化图片 |
| **多参考图** | 支持同时上传最多 14 张参考图片 |
| **模型选择** | 支持 Nano Banana Pro（专业创作）和 Nano Banana 2（快速高效）两种模型切换 |
| **高分辨率** | 支持 1K、2K、4K 三种分辨率 |
| **多纵横比** | 1:1、16:9、9:16、4:3、21:9 等多种比例 |
| **多语言支持** | 支持中英文切换，可配置默认语言 |

### 👥 完整的用户系统
| 功能 | 描述 |
|------|------|
| **用户注册** | 邮箱验证码注册，防止滥用 |
| **用户登录** | 安全的密码验证 |
| **点数系统** | 按分辨率消耗点数，精细化计费 |
| **卡密充值** | 用户可通过卡密自助充值 |
| **会话管理** | 多会话管理，随时切换对话 |

### 🔧 强大的管理后台
| 功能 | 描述 |
|------|------|
| **用户管理** | 查看、删除用户，管理权限 |
| **点数管理** | 为用户手动充值点数 |
| **卡密生成** | 批量生成充值卡密 |
| **数据统计** | 查看用户使用情况 |
| **数据清理** | 清理历史数据释放空间 |

### 🔒 企业级安全
- CSRF 跨站请求伪造防护
- 速率限制防暴力破解
- 密码哈希安全存储
- Session 安全配置
- 路径遍历攻击防护
- 生产环境 HTTPS 强制
- 敏感数据加密存储

### 🛡️ 数据安全声明
**安全声明: 本应用所有数据（用户账号、对话记录、图片等）均加密存储于您部署环境的本地 SQLite 数据库中。**

- 我们不会上传任何数据至第三方服务器
- 您完全掌控自己的数据隐私
- 敏感信息（如 API Key、密码）均经过哈希加密处理

### 🌐 国际化支持
- 支持中文/英文界面一键切换
- 自动检测浏览器语言偏好
- 支持自定义默认语言配置

---

## 🌐 国际化配置

本系统支持多语言切换（目前支持中文和英文）。

### 切换默认语言

默认语言配置在 `static/js/i18n.js` 文件中。你可以修改 `DEFAULT_LANG` 变量来更改默认语言：

1. 打开 `static/js/i18n.js` 文件
2. 找到配置项区域：

```javascript
// ========================================
// 配置项 - 可以在这里修改默认语言
// ========================================
const DEFAULT_LANG = 'zh';  // 默认语言: 'zh' (中文) 或 'en' (英文)
```

3. 将 `'zh'` 修改为 `'en'` 即可将默认语言设置为英文。

### 添加新语言

如果有开发能力，你可以在 `static/js/i18n.js` 的 `translations` 对象中添加新的语言包，并在 `index.html` 中添加对应的切换按钮。

---

## 🚀 快速开始（5 分钟部署）

### 第一步：获取项目代码

```bash
# 克隆仓库
git clone https://github.com/gbmomo/gemini-image-webapp.git

# 进入项目目录
cd gemini-image-webapp
```

### 第二步：安装 Python 环境

确保你的电脑已安装 Python 3.10 或更高版本：

```bash
# 检查 Python 版本
python --version
# 输出应该是 Python 3.10.x 或更高
```

创建虚拟环境（推荐）：

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 第三步：获取 Gemini API Key

1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
2. 登录你的 Google 账号
3. 点击「Create API Key」创建一个新的 API Key
4. 复制生成的 API Key（形如 `AIzaSy...`）

> ⚠️ **重要提示**：请妥善保管你的 API Key，不要泄露给他人！

### 第四步：配置环境变量

1. 创建配置文件（复制一份模板并重命名）：

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

2. 打开刚才创建的 `.env` 文件，填写你的配置：

```env
# ========== 必填项（填这三个就能跑起来！） ==========

# 你的 Gemini API Key（第三步获取的）
GEMINI_API_KEY=AIzaSy你的API密钥

# 随便写一串复杂的字符串，用于加密用户会话
SECRET_KEY=abc123随便写一串复杂的字符

# 管理员密码（登录 admin 账号用）
ADMIN_PASSWORD=你的管理员密码

# ========== 可选配置 ==========

# 使用的 Gemini 模型（默认使用 gemini-3.1-flash-image-preview，即 Nano Banana 2）
# 可选值：gemini-3.1-flash-image-preview（Nano Banana 2，快速高效，默认）
#         gemini-3-pro-image-preview（Nano Banana Pro，专业创作）
# 此设置控制前端默认选中的模型，用户仍可在界面上切换
# GEMINI_MODEL=gemini-3.1-flash-image-preview

# 如果你需要邮箱验证码注册功能，请配置以下内容：
# EMAIL_SENDER=你的邮箱@qq.com
# EMAIL_PASSWORD=邮箱授权码
# SMTP_SERVER=smtp.qq.com
# SMTP_PORT=465
```

> 💡 **小提示**：最简配置只需填写前三项即可运行！邮箱配置可以之后再添加。

### 第五步：启动应用

```bash
python app.py
```

看到以下输出说明启动成功：

```
 * Running on http://127.0.0.1:5000
```

### 第六步：开始使用！

1. 打开浏览器，访问 `http://127.0.0.1:5000`
2. 使用 `admin` + 你设置的管理员密码登录
3. 开始创作你的第一张 AI 图片！

🎉 **恭喜！你已经成功部署了自己的 AI 图片生成网站！**

---

## 📖 详细使用教程

### 👤 普通用户使用流程

#### 1. 注册账号
- 点击「立即注册」
- 输入用户名、邮箱、密码
- 输入邮箱收到的验证码
- 完成注册（新用户赠送 4 点数）

#### 2. 创建对话
- 点击左侧「+ 新对话」按钮
- 给对话起个名字（可选）

#### 3. 选择参数
- **AI 模型**：Nano Banana Pro（专业创作）、Nano Banana 2（快速高效）
- **分辨率**：1K（1点）、2K（2点）、4K（4点）
- **纵横比**：自动、1:1、16:9、9:16 等

> ⚠️ 注意：首次生成后模型、分辨率、纵横比参数会被锁定，需要创建新对话才能更改

#### 4. 生成图片

**文生图**：直接输入描述文字
```
示例：一只可爱的柯基犬在樱花树下奔跑，阳光明媚，日系动漫风格，高清
```

**图生图**：上传参考图片 + 输入描述
```
示例：把图片中的人物换成猫耳娘风格
```

#### 5. 迭代优化
- 生成后可以继续发送消息修改
- AI 会记住之前生成的图片
- 可以说「把背景换成星空」「让色彩更鲜艳」等

#### 6. 下载图片
- 点击生成的图片查看大图
- 点击「下载图片」保存到本地

### 🔧 管理员使用指南

使用 `admin` 账号登录后，点击右上角「管理后台」进入管理控制台。

#### 用户管理
- 查看所有注册用户
- 查看用户的会话和消息数
- 为用户手动充值点数
- 设置/取消管理员权限
- 删除违规用户

#### 卡密管理
- 批量生成充值卡密
- 设置每张卡密的点数
- 查看卡密使用记录
- 卡密生成后请立即复制保存（只显示一次！）

#### 数据清理
- 设置截止日期
- 清理指定日期前的历史数据
- 释放服务器存储空间

---

## 💰 点数消耗说明

| 分辨率 | 像素 | 消耗点数 | 适用场景 |
|--------|------|----------|----------|
| **1K** | 约 1024px | 🪙 1 点 | 快速预览、草图 |
| **2K** | 约 2048px | 🪙 2 点 | 日常使用（推荐） |
| **4K** | 约 4096px | 🪙 4 点 | 高清壁纸、印刷 |

> 💡 管理员账号免费使用，不消耗点数

---

## 🌐 生产环境部署（宝塔面板）

如果你想把网站部署到服务器上供他人访问，推荐使用 **宝塔面板（BT Panel）** 进行部署，操作简单，适合新手。

> 💡 宝塔面板官网：[https://www.bt.cn](https://www.bt.cn)，可参考官方 Python 部署教程：[宝塔面板 Python 网站部署教程](https://www.bt.cn/bbs/thread-144409-1-1.html)

### 前置准备

1. 一台安装了 **Linux 系统**（推荐 Ubuntu 20.04 / CentOS 7.9+）的云服务器
2. 已安装 **宝塔面板**（推荐 9.0+ 版本），安装命令可从 [宝塔官网](https://www.bt.cn/new/download.html) 获取
3. 在宝塔面板中安装 **Nginx**（推荐 1.24+，通过「软件商店」安装）
4. 一个已解析到服务器 IP 的 **域名**

### 第零步：准备 Python 环境

在部署项目之前，需要先在宝塔面板中安装 Python 环境并创建虚拟环境。

#### a. 安装 Python 版本

1. 在宝塔面板左侧菜单，点击 **「网站」**→ **「Python 项目」**
2. 点击右上角 **「环境管理」**
3. 点击 **「版本管理」**
4. 找到 **Python 3.14.3**（或其他 3.10+ 版本），点击 **「安装」**
5. 等待安装完成（需要几分钟）

<p align="center">
  <img src="Display pictures/BT/python版本安装界面.png" alt="Python版本安装界面" width="80%">
</p>

#### b. 创建虚拟环境

安装好 Python 版本后，建议为本项目创建一个**独立的虚拟环境**，避免不同项目之间的依赖包冲突。

1. 在「环境管理」页面，选择已安装的 Python 版本
2. 点击 **「创建虚拟环境」**
3. 填写虚拟环境名称，例如 `gitsay_gemini_nano`
4. 点击确认创建

<p align="center">
  <img src="Display pictures/BT/创建虚拟环境界面.png" alt="创建虚拟环境界面" width="80%">
</p>

> 💡 **为什么要用虚拟环境？**
> 虚拟环境将本项目的依赖包与系统环境隔离，防止不同项目之间的包版本冲突，方便管理和维护。

### 第一步：上传项目代码

1. 登录宝塔面板，进入 **「文件」** 管理
2. 进入 `/www/wwwroot/` 目录
3. 点击 **「上传」**，将整个项目文件夹上传到服务器，例如上传后路径为：
   ```
   /www/wwwroot/gemini-image-webapp
   ```
4. 也可以使用 SFTP 工具（如 WinSCP、FileZilla）上传

> 💡 你也可以在终端中使用 `git clone` 直接拉取项目代码：
> ```bash
> cd /www/wwwroot
> git clone https://github.com/gbmomo/gemini-image-webapp.git
> ```

### 第二步：创建 Python 项目

1. 在宝塔面板左侧菜单，点击 **「网站」**
2. 点击 **「Python 项目」** 标签页
3. 点击 **「添加 Python 项目」**，按以下配置填写：

<p align="center">
  <img src="Display pictures/BT/宝塔面板添加python项目.png" alt="宝塔面板添加Python项目" width="80%">
</p>

| 配置项 | 填写内容 |
|--------|----------|
| **项目名称** | `gemini-image-webapp`（自定义，方便识别） |
| **Python 环境** | 选择 `Python 3.10+`（如无可用环境，点击右侧「环境管理」安装） |
| **启动方式** | 选择 `gunicorn` |
| **项目路径** | `/www/wwwroot/gemini-image-webapp`（你上传的项目路径） |
| **启动命令** | `gunicorn -w 3 -b 0.0.0.0:5000 --timeout 300 app:app` |
| **环境变量** | 选择「指定变量」（第三步详细说明） |
| **启动用户** | `www`（默认即可） |
| **安装依赖包** | 填写 `requirements.txt` 的路径，或留空后手动安装 |

> ⚠️ **启动命令说明**：
> - `-w 3`：开启 3 个 worker 进程（可根据服务器 CPU 核数调整，一般为 `2 * CPU核数 + 1`）
> - `-b 0.0.0.0:5000`：监听所有网卡的 5000 端口
> - `--timeout 300`：超时时间 300 秒（AI 生图需要较长时间，不要设置太短）
> - `app:app`：Flask 应用入口

### 第三步：配置环境变量

在创建项目时，环境变量部分选择 **「指定变量」**，然后逐行添加以下环境变量（也可以在项目创建后，进入项目 **「设置」** 中修改）：

<p align="center">
  <img src="Display pictures/BT/环境变量配置界面.png" alt="环境变量配置界面" width="80%">
</p>

```env
EMAIL_SENDER=你的发件邮箱@example.com
ADMIN_PASSWORD=你的管理员密码
SMTP_SERVER=smtp.exmail.qq.com
EMAIL_PASSWORD=你的邮箱授权码
SMTP_PORT=465
GEMINI_API_KEY=你的Gemini_API_Key
FLASK_ENV=production
SECRET_KEY=你的随机密钥字符串
FLASK_DEBUG=False
```

| 变量名 | 说明 | 是否必填 |
|--------|------|----------|
| `GEMINI_API_KEY` | 你的 Google Gemini API 密钥 | ✅ 必填 |
| `SECRET_KEY` | 随机加密字符串，用于 Session 加密 | ✅ 必填 |
| `ADMIN_PASSWORD` | 管理员登录密码 | ✅ 必填 |
| `FLASK_ENV` | 设置为 `production` | ✅ 必填 |
| `FLASK_DEBUG` | 设置为 `False` | ✅ 必填 |
| `EMAIL_SENDER` | 发件邮箱地址 | 可选（需要注册功能时必填） |
| `EMAIL_PASSWORD` | 邮箱 SMTP 授权码 | 可选 |
| `SMTP_SERVER` | SMTP 服务器地址 | 可选 |
| `SMTP_PORT` | SMTP 端口号（通常为 465） | 可选 |

> ⚠️ **注意**：配置完环境变量后，需要 **重启项目** 才能生效。

### 第四步：启动项目并验证

1. 配置完成后，点击 **「启动」** 或 **「重启」** 按钮
2. 查看项目状态，确认显示为 **「运行中」**
3. 查看项目日志，确认没有报错信息

<p align="center">
  <img src="Display pictures/BT/项目运行状态.png" alt="项目运行状态" width="80%">
</p>

4. 在浏览器中访问 `http://你的服务器IP:5000`，确认网站可以正常访问

> 💡 如果无法访问，请检查：
> - 宝塔面板「安全」中是否已放行 5000 端口
> - 服务器安全组（如阿里云/腾讯云）是否已开放 5000 端口
> - 项目日志中是否有报错信息

### 第五步：配置域名和外网映射

#### 5.1 绑定域名

1. 在 Python 项目列表中，点击项目进入 **「设置」**
2. 找到 **「域名管理」** 部分
3. 添加你的域名，例如 `nano.gitsay.com`

<p align="center">
  <img src="Display pictures/BT/域名绑定界面.png" alt="域名绑定界面" width="80%">
</p>

#### 5.2 开启外网映射

1. 在项目设置中，找到 **「外网映射」** 选项
2. 点击 **「开启外网映射」**，填写以下配置：

<p align="center">
  <img src="Display pictures/BT/外网映射配置.png" alt="外网映射配置" width="80%">
</p>

| 配置项 | 填写内容 |
|--------|----------|
| **代理路由** | `/` |
| **代理端口** | `5000` |

3. 点击保存，宝塔会自动创建一个 Nginx 反向代理网站

### 第六步：配置 SSL 证书（HTTPS）

1. 在宝塔面板左侧菜单，点击 **「网站」**
2. 找到刚才映射创建的网站，点击 **「设置」**
3. 点击左侧 **「SSL」** 标签
4. 可以选择以下方式申请证书：
   - **Let's Encrypt**：免费证书，点击「申请」即可自动签发
   - **宝塔证书**：宝塔提供的免费证书
   - **其他证书**：如果你已有证书，可以粘贴 PEM 格式的证书和密钥

<p align="center">
  <img src="Display pictures/BT/SSL证书申请.png" alt="SSL证书申请界面" width="80%">
</p>

5. 证书申请成功后，开启 **「强制 HTTPS」**

### 第七步：优化 Nginx 配置（推荐）

网站创建后，你可以通过 **「设置」→「配置文件」** 来优化 Nginx 配置，以更好地支持 AI 图片生成服务。

以下是一份推荐的配置参考，你可以根据自己的实际情况进行修改：

```nginx
server
{
    listen 80;
    listen 443 ssl;
    listen 443 quic;
    http2 on;
    server_name 你的域名.com;
    index index.html index.htm default.htm default.html;
    root /www/wwwroot/gemini-image-webapp;

    #SSL-START SSL相关配置
    ssl_certificate    /www/server/panel/vhost/cert/你的网站名/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/你的网站名/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:!MD5:!3DES;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    error_page 497  https://$host$request_uri;
    #SSL-END

    # --- 安全增强 Headers ---
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # --- 上传大小限制 (允许最大 50MB) ---
    client_max_body_size 50M;

    # --- 强制 HTTP 跳转 HTTPS ---
    if ($scheme = http) {
        return 301 https://$host$request_uri;
    }

    # 禁止访问的敏感文件
    location ~* (\.env.*|\.git|\.htaccess|\.user\.ini|\.DS_Store|README\.md|requirements\.txt|\.py$)
    {
        return 404;
    }

    # --- 健康检查端点 ---
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }

    # --- 反向代理到 Python 应用 ---
    location / {
        proxy_pass http://127.0.0.1:5000;

        # 代理头部设置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header REMOTE-HOST $remote_addr;

        # WebSocket 支持（流式输出需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置 - AI 生成需要较长时间
        proxy_connect_timeout 180s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;
    }

    access_log  /www/wwwlogs/你的网站名.log;
    error_log  /www/wwwlogs/你的网站名.error.log;
}
```

> ⚠️ **重要提示**：
> - 请将 `你的域名.com` 和 `你的网站名` 替换为你的实际域名和网站名称
> - SSL 证书路径以宝塔面板实际生成的为准
> - 超时时间建议设为 180 秒以上，AI 图片生成需要较长处理时间

### 第八步：最终验证

1. 在浏览器中访问 `https://你的域名.com`
2. 确认 HTTPS 证书正常工作（地址栏显示🔒）
3. 使用 `admin` + 你设置的管理员密码登录
4. 尝试生成一张图片，确认所有功能正常

🎉 **恭喜！你已经通过宝塔面板成功部署了 AI 图片生成网站！**

### 其他部署方式

除宝塔面板外，你还可以使用以下方式部署：

- **Gunicorn + Nginx 手动部署**：适合有 Linux 服务器运维经验的用户
- **Docker / Docker Compose**：适合熟悉容器化部署的用户
- **1Panel 面板**：另一款开源服务器管理面板，操作类似

> 💡 如需其他部署方式的详细教程，可以询问 AI 助手或搜索相关资料。

## 📁 项目结构说明

```
gemini-image-webapp/
│
├── 📄 app.py                 # 主程序入口（Flask 应用）
├── 📄 database.py            # 数据库操作（用户、卡密等）
├── 📄 email_service.py       # 邮件服务（验证码发送）
├── 📄 requirements.txt       # Python 依赖列表
├── 📄 .env                   # 环境变量配置（需自己创建）
├── 📄 .env.example           # 环境变量模板
├── 📄 .gitignore             # Git 忽略规则
│
├── 📁 data/                  # 数据目录（自动生成）
│   ├── users.db              # SQLite 用户数据库
│   └── sessions/             # 用户会话 JSON 文件
│
├── 📁 static/                # 静态资源
│   ├── css/                  # 样式文件
│   ├── js/                   # JavaScript 脚本
│   ├── fonts/                # 字体文件
│   ├── lib/                  # 第三方库（如日期选择器）
│   ├── logo.ico              # 网站图标
│   ├── images/               # 生成的图片（自动创建）
│   └── thumbnails/           # 缩略图（自动创建）
│
└── 📁 templates/             # HTML 模板
    ├── index.html            # 用户主页面
    └── admin.html            # 管理后台页面
```

---

## ❓ 常见问题

### Q: 生成图片很慢/超时怎么办？
**A:** Gemini 图片生成通常需要 30-60 秒，这是正常的。如果经常超时：
- 检查网络连接是否稳定
- 可以配置 `GEMINI_API_BASE_URL` 使用代理
- 减少参考图片数量

### Q: 验证码邮件收不到？
**A:** 
- 检查垃圾邮件文件夹
- 确认邮箱配置正确（使用授权码而非登录密码）
- QQ 邮箱需要先开启 SMTP 服务

### Q: 如何使用代理访问 Gemini API？
**A:** 

**本地开发环境**：在 `.env` 文件中配置：
```env
GEMINI_API_BASE_URL=http://你的代理地址:端口
```

**服务器部署环境（宝塔面板）**：在宝塔面板的 Python 项目设置中，找到「环境变量」，添加：
```env
GEMINI_API_BASE_URL=http://你的代理地址:端口
```
添加后需要 **重启项目** 才能生效。

> ⚠️ **重要提示：本项目使用 Gemini 官方 API 协议**
> 
> 本项目调用的 API 必须遵循 **Google Gemini 官方 API 协议格式**，例如：
> - `http://127.0.0.1:8045/v1beta/models`
> - `https://generativelanguage.googleapis.com/v1beta/models`
> 
> 如果你使用第三方 API 代理服务，请确保该服务完全兼容 Gemini API 协议（`/v1beta/models` 端点格式），而非 OpenAI API 格式。
> 
> 配置示例：
> ```env
> GEMINI_API_BASE_URL=http://127.0.0.1:8045
> GEMINI_API_KEY=你的API密钥
> ```

### Q: 如何关闭邮箱验证注册？
**A:** 目前版本需要修改源码。在 `app.py` 的 `api_register` 函数中注释掉验证码校验逻辑。

### Q: 忘记管理员密码怎么办？
**A:** 管理员密码是通过环境变量 `ADMIN_PASSWORD` 设置的：
- **本地开发**：修改 `.env` 文件中的 `ADMIN_PASSWORD` 值，然后重启应用
- **服务器部署（宝塔面板）**：在宝塔面板的 Python 项目设置中，修改环境变量 `ADMIN_PASSWORD` 的值，然后重启项目

---

## 🔧 API 接口文档

<details>
<summary>点击展开完整 API 文档</summary>

### 认证接口

| 接口 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/login` | POST | 用户登录 | `username`, `password` |
| `/api/register` | POST | 用户注册 | `username`, `email`, `password`, `verification_code` |
| `/api/logout` | GET | 用户登出 | - |
| `/api/send-verification-code` | POST | 发送验证码 | `email` |

### 会话接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/sessions` | GET | 获取会话列表 |
| `/api/sessions` | POST | 创建新会话 |
| `/api/sessions/<id>` | GET | 获取会话详情 |
| `/api/sessions/<id>` | DELETE | 删除会话 |
| `/api/sessions/<id>/title` | PUT | 更新会话标题 |

### 生成接口

| 接口 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/generate` | POST | 生成图片 | `session_id`, `prompt`, `aspect_ratio`, `image_size`, `model`, `reference_images` |
| `/api/models` | GET | 获取可用模型列表 | - |
| `/api/redeem` | POST | 卡密充值 | `code` |

### 管理员接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/admin/users` | GET | 获取用户列表 |
| `/api/admin/users/<id>` | DELETE | 删除用户 |
| `/api/admin/users/<id>/credits` | POST | 充值点数 |
| `/api/admin/users/<id>/toggle-admin` | POST | 切换管理员权限 |
| `/api/admin/card-keys` | GET | 获取卡密列表 |
| `/api/admin/card-keys` | POST | 生成卡密 |
| `/api/admin/cleanup` | POST | 清理历史数据 |

</details>

---

## ⚠️ 注意事项

1. **API Key 安全**
   - 切勿将 `.env` 文件提交到 Git
   - 不要在公开场合分享你的 API Key

2. **数据备份**
   - 定期备份 `data/` 目录
   - 包含用户数据和会话记录

3. **生产环境**
   - 务必使用 HTTPS
   - 设置 `FLASK_ENV=production`
   - 使用 Gunicorn 而非 Flask 开发服务器

4. **API 配额**
   - 注意 Google Gemini API 的免费配额限制
   - 超出配额需要付费或等待刷新

---

## 📢 反馈

如有问题或建议，欢迎提交 [Issue](https://github.com/gbmomo/gemini-image-webapp/issues)！

---

## 📄 开源许可

本项目采用 [CC BY-NC-SA 4.0 许可证](LICENSE) 开源。
严禁任何形式的商业行为。

**如果想商用，请联系作者购买商用许可。**

---

## 📞 联系

- **Email**: S@gitsay.com
- **QQ**: 550948321
- **WeChat**: Goblin_MoMo
- **GitHub**: [@gbmomo](https://github.com/gbmomo)
