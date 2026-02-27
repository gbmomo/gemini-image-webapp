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

# 使用的 Gemini 模型（默认使用 gemini-3-pro-image-preview）
# 可选值：gemini-3-pro-image-preview（Nano Banana Pro）、gemini-3.1-flash-image-preview（Nano Banana 2）
# 此设置控制前端默认选中的模型，用户仍可在界面上切换
# GEMINI_MODEL=gemini-3-pro-image-preview

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

## 🌐 生产环境部署

如果你想把网站部署到服务器上供他人访问，请参考以下步骤：

### 方式一：1Panel 面板部署（推荐）

#### 1. 上传项目代码
通过 1Panel 文件管理器或 SFTP 将项目代码上传到服务器，例如 `/python-envs/nano-banana`

#### 2. 创建运行环境
进入 1Panel →「网站」→「运行环境」→「创建运行环境」，填写：

| 配置项 | 填写内容 |
|--------|----------|
| **名称** | nano-banana（自定义） |
| **项目目录** | 选择你上传的项目路径 |
| **启动命令** | `pip install -r requirements.txt && gunicorn -w 6 -b 0.0.0.0:5000 --timeout 300 app:app` |
| **应用** | Python 3.10+ |
| **容器名称** | nano-banana（自定义） |

#### 3. 配置环境变量
切换到「环境变量」标签页，点击添加，依次填入以下变量：

| 变量名 | 说明 |
|--------|------|
| `GEMINI_API_KEY` | 你的 Gemini API 密钥 |
| `SECRET_KEY` | 随机字符串，用于加密会话 |
| `ADMIN_PASSWORD` | 管理员密码 |
| `FLASK_DEBUG` | `False` |
| `EMAIL_SENDER` | 发件邮箱（可选） |
| `EMAIL_PASSWORD` | 邮箱授权码（可选） |
| `SMTP_SERVER` | SMTP 服务器（可选） |
| `SMTP_PORT` | SMTP 端口（可选） |

#### 4. 配置端口
切换到「端口」标签页，添加端口映射：`5000`

#### 5. 创建网站并配置反向代理
- 进入「网站」→「创建网站」→「反向代理」
- 填写域名，代理地址填 `http://127.0.0.1:5000`
- 申请 SSL 证书，开启 HTTPS

### 其他部署方式

除 1Panel 外，你还可以使用以下方式部署：

- **Gunicorn + Nginx**：适合有 Linux 服务器运维经验的用户
- **Docker / Docker Compose**：适合熟悉容器化部署的用户
- **宝塔面板**：操作方式与 1Panel 类似

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
**A:** 在 `.env` 中配置：
```env
GEMINI_API_BASE_URL=http://你的代理地址:端口
```

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
**A:** 删除 `data/users.db` 文件，重启应用会自动创建新的管理员账号。

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
