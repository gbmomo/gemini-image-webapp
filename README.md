# Gemini Nano Banana AI 图片生成网站

<p align="center">
  <b>简体中文</b> | <a href="README_EN.md">English</a>
</p>

<p align="center">
  <img src="static/logo.ico" alt="Logo" width="120" height="120">
</p>

<p align="center">
  基于 Flask 和 Gemini 图像模型的自托管图片生成网站，包含用户、点数、会话、卡密和管理后台。
</p>

<p align="center">
  <a href="https://nano.gitsay.com/">在线演示</a> ·
  <a href="https://github.com/gbmomo/gemini-image-webapp">项目仓库</a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/gbmomo/gemini-image-webapp?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/gbmomo/gemini-image-webapp?style=flat-square" alt="Forks">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg" alt="License">
</p>

> 本项目采用 [CC BY-NC-SA 4.0](LICENSE) 许可证。使用时必须署名原作者 [@gbmomo](https://github.com/gbmomo)，并提供[原项目链接](https://github.com/gbmomo/gemini-image-webapp)；未经单独授权不得商用，修改后的作品须以相同许可证发布。商用授权联系：S@gitsay.com，QQ：550948321，微信：Goblin_MoMo。

## 当前功能

- 文生图、参考图生图和带上下文的多轮图片迭代。参考图可通过文件选择、拖拽或粘贴添加。
- 每个用户可创建、切换和删除多个会话；首轮成功后以提示词前 20 个字符自动命名，并锁定模型、分辨率和比例，如需更改必须新建会话。后端另提供标题修改接口，但当前界面没有重命名入口。
- 提供中文和英文切换，默认语言在 `static/js/i18n.js` 的 `DEFAULT_LANG` 中设置。
- 邮箱验证码注册、用户名密码登录、退出登录和基于签名 Cookie 的登录会话。
- 新用户默认赠送 4 点；普通用户按“模型 + 分辨率”扣点，管理员生成不扣点。
- 卡密自助充值；管理员可批量生成卡密并查看使用情况。
- 后台管理用户、权限、点数、会话、消息、API/SMTP 设置和模型价格。
- 历史数据清理、孤儿图片清理、缩略图、文件锁和生成扣费恢复。
- CSRF、防暴力限流、上传校验、资源所有权校验及生产环境 HTTPS/安全响应头。
- 生成图点击预览和下载、`Ctrl+Enter` 快速提交，以及适配窄屏的会话侧栏。

注册要求用户名唯一且为 3 到 64 个字符，邮箱唯一且不超过 254 个字符，密码为 6 到 256 个字符并同时包含字母和数字。验证码为 6 位数字、10 分钟有效且只能使用一次。

## 模型能力

模型、分辨率、比例和参考图数量都由后端能力矩阵校验，不只是前端选项限制。

| 模型 ID | 界面名称 | 分辨率 | 最大参考图数 | 支持比例 |
|---|---|---:|---:|---|
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | 1K | 14 | 通用比例 |
| `gemini-3.1-flash-image` | Nano Banana 2 | 512、1K、2K、4K | 14 | 通用比例，另含 1:4、1:8、4:1、8:1 |
| `gemini-3-pro-image` | Nano Banana Pro | 1K、2K、4K | 14 | 通用比例 |
| `gemini-2.5-flash-image` | Nano Banana | 1K | 3 | 通用比例 |

通用比例为：`1:1`、`2:3`、`3:2`、`3:4`、`4:3`、`4:5`、`5:4`、`9:16`、`16:9`、`21:9`。

新会话在当前界面中默认使用后台选定的默认模型、`1K` 和 `1:1`；`auto` 比例仅为历史会话兼容保留。

参考图支持 PNG、JPEG、GIF、WEBP 和 ICO。默认限制为单张 10 MiB、单次请求合计 35 MiB、单张最多 4000 万像素；提示词最多 100000 个字符。这些大小限制可通过环境变量调整。API 响应包含多张图片时，当前实现只保存第一张，统一输出为 PNG，并生成 JPEG 缩略图。

## 点数与扣费

未在后台设置价格时使用以下默认值：

| 分辨率 | 默认点数 |
|---|---:|
| 512 | 1 |
| 1K | 1 |
| 2K | 2 |
| 4K | 4 |

管理员可按每个模型支持的分辨率分别设置 `0` 到 `100000` 点；价格为 `0` 时普通用户也可免费生成。

普通用户生成前会原子预留点数。只有图片成功生成并写入会话后才提交扣费；API 失败、只返回文本、返回空内容或保存失败时会退款并清理本次文件。持久化扣费账本会对进程崩溃留下的过期预留自动对账。同一会话的生成请求通过跨进程文件锁串行执行，避免历史消息互相覆盖。

## 快速开始

要求 Python 3.10 或更高版本。

```bash
git clone https://github.com/gbmomo/gemini-image-webapp.git
cd gemini-image-webapp

python -m venv .venv
```

激活虚拟环境并安装依赖：

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

复制配置模板：

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

至少设置以下两项：

```env
SECRET_KEY=请替换为高强度随机字符串
ADMIN_PASSWORD=请替换为管理员密码
```

可用下面的命令生成 `SECRET_KEY`：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

启动应用：

```bash
python app.py
```

访问 `http://127.0.0.1:5000`，用账号 `admin` 和 `ADMIN_PASSWORD` 登录，再进入管理后台配置 Gemini API 和 SMTP。也可以直接在 `.env` 中设置 `GEMINI_API_KEY` 及邮件参数。

`ADMIN_PASSWORD` 会在应用启动时同步到已有的 `admin` 账号。首次启动未配置它时，程序会生成随机密码并写入启动日志；生产环境应始终显式配置。

## 环境变量

后台保存的 API 设置整体优先于 `GEMINI_*` 环境变量，后台默认模型优先于 `DEFAULT_MODEL`；SMTP 的发件人、密码、服务器和端口则分别按“数据库非空值优先，否则回退环境变量”解析。完整模板见 [.env.example](.env.example)。

### 基础与 API

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SECRET_KEY` | 无 | Flask Session 和 CSRF 签名密钥，必须设置 |
| `ADMIN_PASSWORD` | 首次启动随机生成 | `admin` 账号密码，生产环境必须设置 |
| `GEMINI_API_KEY` | 空 | Gemini API Key；也可在后台保存 |
| `GEMINI_API_BASE_URL` | 空 | 自定义兼容端点；设置后环境变量模式使用 `custom` Provider |
| `DEFAULT_MODEL` | `gemini-3.1-flash-image` | 默认模型，必须是上表中的模型 ID |
| `FLASK_ENV` | `development` | 设为 `production` 时强制 HTTPS 并启用生产安全头 |
| `FLASK_DEBUG` | `False` | Flask 调试模式；生产环境保持关闭 |

### 邮件

| 变量 | 默认值 | 说明 |
|---|---|---|
| `EMAIL_SENDER` | 空 | SMTP 发件账号 |
| `EMAIL_PASSWORD` | 空 | SMTP 密码或授权码 |
| `SMTP_SERVER` | 空 | SMTP 服务器 |
| `SMTP_PORT` | `465` | SMTP SSL 端口 |
| `SMTP_TIMEOUT` | `15` | SMTP 连接超时秒数 |

### 部署、存储与限制

| 变量 | 默认值 | 说明 |
|---|---|---|
| `TRUST_PROXY_COUNT` | `0` | 可信反向代理层数；单层 Nginx 通常设为 `1` |
| `RATELIMIT_STORAGE_URI` | `memory://` | 限流存储；多 worker 必须改为 Redis 等共享后端 |
| `DATABASE_FILE` | `data/users.db` | SQLite 文件路径 |
| `DATA_DIR` | `data` | 会话 JSON 和锁文件目录 |
| `IMAGES_DIR` | `static/images` | 生成图及参考图目录 |
| `THUMBNAILS_DIR` | `static/thumbnails` | 缩略图目录 |
| `DATABASE_BUSY_TIMEOUT_MS` | `5000` | SQLite 忙等待毫秒数 |
| `MAX_REQUEST_BYTES` | `52428800` | HTTP 请求体上限，默认 50 MiB |
| `MAX_REFERENCE_IMAGE_BYTES` | `10485760` | 单张参考图上限，默认 10 MiB |
| `MAX_REFERENCE_TOTAL_BYTES` | `36700160` | 单次请求参考图总上限，默认 35 MiB |
| `MAX_REFERENCE_PIXELS` | `40000000` | 单张参考图最大像素数 |
| `GENERATION_CHARGE_TTL_SECONDS` | `900` | 待处理扣费的恢复窗口，代码强制最低 600 秒 |
| `GENERATION_LOCK_TIMEOUT` | `330` | 等待同一会话生成锁的秒数 |
| `DISABLE_BACKGROUND_TASKS` | `false` | 设为 `true` 时关闭应用内后台清理线程 |
| `CHAT_IDLE_TIMEOUT` | `1800` | 进程内 Gemini 聊天缓存闲置时间，秒 |
| `CHAT_CLEANUP_INTERVAL` | `600` | 后台清理检查间隔，秒 |

`DATA_DIR` 只控制会话目录和维护锁位置；SQLite 位置始终由独立的 `DATABASE_FILE` 控制。

## 管理后台

管理员访问 `/admin` 可使用以下功能：

- 查看用户、角色、余额、会话数和消息数，并查看某个用户的会话及消息详情。
- 给用户增加或扣除点数，但扣除后余额不能低于 0。
- 授予或取消管理员权限；主管理员 `admin` 的角色不能修改。
- 删除普通用户及其会话和关联图片；管理员账号不能删除。
- 每批生成 1 到 100 张卡密，每张点数必须大于 0。完整卡密只在生成响应中显示一次，之后仅显示前缀和使用记录。
- 按日期清理历史消息、空会话、关联文件及孤儿文件，或清理全部会话数据。
- 在 Google AI Studio 和自定义 URL 两种 Provider 间切换，设置 API Key、自定义 URL 和默认模型。
- 设置发件邮箱、SMTP 密码、服务器和端口。
- 按模型和分辨率编辑点数价格。设置保存后当前进程立即重建客户端，其他 worker 会根据配置版本自动刷新。

当前充值弹窗中的“前往购买”按钮固定指向 `https://pay.ldxp.cn/shop/momo/fhrvq4`。自行部署时应在 `templates/index.html` 中替换为自己的购买地址，或移除该按钮；卡密兑换本身在本地完成。顶部的“`$0.04起/张`”也是 `static/js/i18n.js` 中的固定展示文案，不会随后台点数价格变化。

## 数据存储与安全边界

| 数据 | 存储位置 | 实际保护方式 |
|---|---|---|
| 用户、验证码、卡密、API/SMTP 设置、价格、扣费账本 | SQLite，默认 `data/users.db` | 密码和验证码使用带盐哈希；卡密保存验证哈希、SHA-256 查找值和前缀 |
| 会话与消息 | `data/sessions/user_<id>.json` | 本地明文 JSON；文件锁、临时文件、`fsync` 和原子替换 |
| 生成图、参考图、缩略图 | `static/images`、`static/thumbnails` | 本地明文文件；HTTP 访问仅允许文件所有者或管理员 |

请注意以下边界：

- API Key、SMTP 密码、邮箱、会话 JSON 和图片没有静态加密。它们依赖部署机器的文件权限、磁盘加密和备份策略保护。
- Flask Session Cookie 是签名数据，不应把 `SECRET_KEY` 理解为数据库或文件加密密钥。
- 生成时，提示词、会话上下文和参考图会发送给配置的 Gemini/API Provider；注册时，收件邮箱和验证码会发送给配置的 SMTP 服务。部署者需要按所用服务商条款向用户说明数据处理方式。
- 应备份 SQLite 数据库、`data/sessions`、图片和缩略图目录；只备份数据库不能恢复完整历史。

应用还启用了以下保护：所有非安全 HTTP 方法进行 CSRF 校验，Token 有效期为 1 小时；Session Cookie 为 `HttpOnly`、`SameSite=Lax`，生产模式下为 `Secure`；登录 `5/分钟`、验证码 `1/分钟`、注册 `3/小时`、生成 `20/小时`，全局默认 `100/小时` 和 `1000/天`，均按客户端 IP 限制；上传内容会进行 Base64、格式、大小和像素校验。

## 生产部署

推荐使用 Gunicorn 放在 Nginx 等 HTTPS 反向代理之后。Gemini SDK 超时为 300 秒，因此 Gunicorn 和反向代理超时应更长：

```bash
gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 --timeout 360 app:app
```

单层 Nginx 的关键配置示例：

```nginx
server {
    listen 443 ssl;
    server_name example.com;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 360s;
        proxy_send_timeout 360s;
        proxy_read_timeout 360s;
    }
}
```

同时设置 `FLASK_ENV=production`、`FLASK_DEBUG=False` 和 `TRUST_PROXY_COUNT=1`。`TRUST_PROXY_COUNT` 只能等于实际可信代理层数，不要在应用直接暴露公网时启用。确保运行用户可写数据库、`DATA_DIR`、`IMAGES_DIR` 和 `THUMBNAILS_DIR`。

默认 `memory://` 限流只适合单 worker。使用多个 worker 时配置 Redis，例如 `RATELIMIT_STORAGE_URI=redis://127.0.0.1:6379/0`。应用没有 WebSocket 或流式输出要求。

## HTTP 路由总览

所有 `POST`、`PUT`、`DELETE` 请求都需要有效 CSRF Token。网页会从 `<meta name="csrf-token">` 读取 Token 并通过 `X-CSRFToken` 发送；自行调用 API 时也必须保留同一浏览器 Session Cookie 和 Token。

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| GET | `/` | 公开 | 主页面，同时签发 CSRF Session |
| GET | `/login` | 公开 | 重定向到主页面 |
| GET | `/api/models` | 公开 | 模型能力、价格及默认模型 |
| POST | `/api/login` | 公开 | 登录 |
| POST | `/api/send-verification-code` | 公开 | 发送注册验证码 |
| POST | `/api/register` | 公开 | 注册用户 |
| POST | `/api/logout` | 登录 | 退出登录并返回 302 页面重定向 |
| GET / POST | `/api/sessions` | 登录 | 获取或创建会话 |
| GET / DELETE | `/api/sessions/<session_id>` | 登录 | 获取或删除会话 |
| PUT | `/api/sessions/<session_id>/title` | 登录 | 修改会话标题 |
| POST | `/api/generate` | 登录 | 生成或迭代图片 |
| POST | `/api/redeem` | 登录 | 使用卡密充值 |
| GET | `/static/images/<filename>` | 文件所有者或管理员 | 获取生成图或参考图 |
| GET | `/static/thumbnails/<filename>` | 文件所有者或管理员 | 获取缩略图 |
| GET | `/admin` | 管理员 | 管理后台页面 |
| GET | `/api/admin/users` | 管理员 | 用户及统计列表 |
| DELETE | `/api/admin/users/<id>` | 管理员 | 删除普通用户 |
| POST | `/api/admin/users/<id>/toggle-admin` | 管理员 | 切换角色 |
| POST | `/api/admin/users/<id>/credits` | 管理员 | 增减点数 |
| GET | `/api/admin/users/<id>/sessions` | 管理员 | 查看用户会话 |
| GET | `/api/admin/users/<id>/sessions/<session_id>` | 管理员 | 查看消息详情 |
| POST | `/api/admin/cleanup` | 管理员 | 清理历史数据和孤儿文件 |
| GET / POST | `/api/admin/card-keys` | 管理员 | 查看或生成卡密 |
| GET / POST | `/api/admin/api-settings` | 管理员 | 查看或保存 API/SMTP 设置 |
| GET / PUT | `/api/admin/model-pricing` | 管理员 | 查看或保存模型价格 |

主要 JSON 写入字段如下：登录为 `username`、`password`；发验证码为 `email`；注册为 `username`、`email`、`password`、`verification_code`；修改标题为 `title`；生成图片为 `session_id`、`prompt`、`model`、`image_size`、`aspect_ratio`、`reference_images`；兑换为 `code`；管理员点数调整为 `amount`；清理为 `cutoff_date`；生成卡密为 `credits`、`count`；API/SMTP 设置为 `provider`、`api_key`、`custom_base_url`、`default_model`、`email_sender`、`email_password`、`smtp_server`、`smtp_port`；模型定价为 `prices` 数组，其中每项包含 `model_id`、`image_size`、`credits`。

## 项目结构

```text
app.py                 Flask 应用、路由、生成与会话逻辑
database.py            SQLite 初始化、迁移、用户、卡密、定价与扣费
email_service.py       SMTP 验证码邮件
templates/             主页面和管理后台模板
static/js/             认证、生成、后台、弹窗和中英文文案
static/css/            页面样式
data/                   SQLite、会话 JSON 和锁文件（运行时创建）
static/images/          生成图和参考图（运行时创建）
static/thumbnails/      缩略图（运行时创建）
tests/                  unittest 回归测试
Display pictures/       README 截图
```

## 测试

测试使用独立临时数据库和存储目录，不应指向真实 `data/users.db`：

```bash
python -m unittest discover -v
```

## 截图

<p align="center">
  <img src="Display pictures/中文/登录界面.png" alt="登录界面" width="45%">
  <img src="Display pictures/中文/注册页面.png" alt="注册页面" width="45%">
</p>

<p align="center">
  <img src="Display pictures/中文/网站首页（生成图片的效果）.png" alt="图片生成效果" width="80%">
</p>

<p align="center">
  <img src="Display pictures/中文/管理员后台首页.png" alt="管理员后台" width="80%">
</p>

## 常见问题

**提示“API 未配置”**：用 `admin` 登录后在管理后台保存 API Key，或设置 `GEMINI_API_KEY` 并重启。

**无法发送注册验证码**：确认发件账号、密码/授权码、SMTP 服务器和端口四项均已配置；当前邮件客户端使用 SMTP over SSL。

**提示“页面验证已失效”**：刷新页面后重试，并确认请求保留 Cookie 且携带当前页面的 `X-CSRFToken`。登录、注册等公开写接口同样需要 CSRF Token。

**多 worker 下限流不一致**：把 `RATELIMIT_STORAGE_URI` 指向所有 worker 共用的 Redis，并重启全部 worker。

## 许可证

[CC BY-NC-SA 4.0](LICENSE)。未经单独商业授权，不得将本项目用于商业用途。
