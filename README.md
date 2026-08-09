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

## 快速导航

[当前功能](#当前功能) · [快速开始](#快速开始) · [环境变量](#环境变量) · [宝塔面板部署](#宝塔面板部署新手推荐) · [安全边界](#数据存储与安全边界) · [常见问题](#常见问题)

## 当前功能

- 文生图、参考图生图和带上下文的多轮图片迭代。参考图可通过文件选择、拖拽或粘贴添加。
- 首页允许匿名浏览、填写提示词和选择生成参数；新建会话、上传参考图或生成图片时才要求登录。匿名草稿会在登录后恢复，但不会自动生成或扣点。
- 每个用户可创建、切换和删除多个会话；首轮成功后以提示词前 20 个字符自动命名，并锁定模型、思考强度、分辨率和比例，如需更改必须新建会话。后端另提供标题修改接口，但当前界面没有重命名入口。
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

模型、思考强度、分辨率、比例和参考图数量都由后端能力矩阵校验，不只是前端选项限制。

| 模型 ID | 界面名称 | 分辨率 | 思考强度 | 最大参考图数 | 支持比例 |
|---|---|---:|---|---:|---|
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | 1K | `minimal`、`high` | 14 | 通用比例 |
| `gemini-3.1-flash-image` | Nano Banana 2 | 512、1K、2K、4K | `minimal`、`high` | 14 | 通用比例，另含 1:4、1:8、4:1、8:1 |
| `gemini-3-pro-image` | Nano Banana Pro | 1K、2K、4K | 自动，不可调整 | 14 | 通用比例 |
| `gemini-2.5-flash-image` | Nano Banana | 1K | 不可调整 | 3 | 通用比例 |

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

至少设置以下三项：

```env
SECRET_KEY=请替换为高强度随机字符串
ADMIN_PASSWORD=请替换为管理员密码
CREDENTIAL_ENCRYPTION_KEY=请替换为独立的Fernet密钥
```

可用下面的命令生成 `SECRET_KEY`：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

用于加密后台 API/SMTP 凭据的密钥必须独立生成，不要复用 `SECRET_KEY`：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

启动应用：

```bash
python app.py
```

访问 `http://127.0.0.1:5000`，用账号 `admin` 和 `ADMIN_PASSWORD` 登录，再进入管理后台配置 Gemini API 和 SMTP。也可以直接在 `.env` 中设置 `GEMINI_API_KEY` 及邮件参数。

`ADMIN_PASSWORD` 会在应用启动时同步到已有的 `admin` 账号。未配置时应用会拒绝启动；生产环境要求至少 12 个字符，并包含至少三类字符。

## 环境变量

后台保存的 API 设置整体优先于 `GEMINI_*` 环境变量，后台默认模型优先于 `DEFAULT_MODEL`；SMTP 的发件人、密码、服务器和端口则分别按“数据库非空值优先，否则回退环境变量”解析。完整模板见 [.env.example](.env.example)。

### 基础与 API

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SECRET_KEY` | 无 | Flask Session 和 CSRF 签名密钥，必须设置 |
| `ADMIN_PASSWORD` | 无 | `admin` 账号密码，必须设置；生产环境至少 12 个字符和三类字符 |
| `CREDENTIAL_ENCRYPTION_KEY` | 无 | 后台数据库凭据的独立 Fernet 密钥；使用后台 API/SMTP 设置时必须设置 |
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
| 用户、验证码、卡密、API/SMTP 设置、价格、扣费账本 | SQLite，默认 `data/users.db` | 密码和验证码使用带盐哈希；卡密保存验证哈希、SHA-256 查找值和前缀；API Key 与 SMTP 密码使用 Fernet 加密 |
| 会话与消息 | `data/sessions/user_<id>.json` | 本地明文 JSON；文件锁、临时文件、`fsync` 和原子替换 |
| 生成图、参考图、缩略图 | `static/images`、`static/thumbnails` | 本地明文文件；HTTP 访问仅允许文件所有者或管理员 |

请注意以下边界：

- API Key 和 SMTP 密码使用 `CREDENTIAL_ENCRYPTION_KEY` 加密后保存；该密钥必须与数据库和备份分开保管。邮箱、会话 JSON 和图片仍依赖部署机器的文件权限、磁盘加密和备份策略保护。
- Flask Session Cookie 是签名数据，不应把 `SECRET_KEY` 理解为数据库或文件加密密钥。
- 每次保存 API/SMTP 设置只保留当前配置；首次使用新版本启动会加密当前配置、删除历史配置并重写 SQLite 页面。升级前仍应轮换曾经明文保存过的第三方凭据，并清理旧备份。
- 生成时，提示词、会话上下文和参考图会发送给配置的 Gemini/API Provider；注册时，收件邮箱和验证码会发送给配置的 SMTP 服务。部署者需要按所用服务商条款向用户说明数据处理方式。
- 应备份 SQLite 数据库、`data/sessions`、图片和缩略图目录；只备份数据库不能恢复完整历史。

应用还启用了以下保护：所有非安全 HTTP 方法进行 CSRF 校验，Token 有效期为 1 小时；Session Cookie 为 `HttpOnly`、`SameSite=Lax`，生产模式下为 `Secure`；登录 `5/分钟`、验证码 `1/分钟`、注册 `3/小时`、生成 `20/小时`，全局默认 `100/小时` 和 `1000/天`，均按客户端 IP 限制；上传内容会进行 Base64、格式、大小和像素校验。

## 生产部署

推荐的部署结构是：浏览器通过 HTTPS 访问 Nginx，Nginx 再把请求转发给只监听本机 `127.0.0.1:5000` 的 Gunicorn。不要直接使用 `python app.py` 对外提供生产服务，也不需要向公网开放 5000 端口。

对于个人站点和中小流量服务器，推荐先使用下面的单 worker、多线程配置：

```bash
gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 --timeout 360 app:app
```

- `-w 1` 表示一个应用进程，默认内存限流可以正常工作，不需要 Redis。
- `--threads 8` 表示该进程可以并行等待多个网络请求，并不等于网站只能供一个用户使用。
- `--timeout 360` 为 AI 生图留出足够时间，Nginx 的发送和读取超时也应设置为 360 秒。

### 宝塔面板部署（新手推荐）

下面的步骤适用于 Linux 服务器上的宝塔面板。不同宝塔版本的按钮名称可能略有差异，但配置项含义相同。

> 截图使用当前宝塔界面，敏感值均已打码。截图中的 `GitSay_Gemini_nano` 是部署示例；实际填写时，项目名称和路径可以不同，但同一处配置中的路径必须互相对应。

#### 1. 准备服务器和域名

开始前请准备：

1. 一台已安装宝塔面板的 Linux 服务器。
2. 在宝塔「软件商店」中安装 Nginx。
3. 一个已通过 A/AAAA 记录解析到服务器的域名。
4. 项目代码和一个可用的 Gemini API Key，或兼容 Gemini API 协议的自定义服务。

建议先备份旧版本的 `data/`、`static/images/` 和 `static/thumbnails/`。如果迁移已有数据库，还必须保留原来的 `CREDENTIAL_ENCRYPTION_KEY`，否则已加密的 API/SMTP 凭据无法解密。

#### 2. 安装 Python 并创建虚拟环境

进入宝塔的「网站」→「Python 项目」→「Python 环境管理」→「版本管理」，安装 Python 3.10 或更高版本。

<p align="center">
  <img src="Display pictures/BT/python版本安装界面.png" alt="宝塔 Python 版本安装界面" width="80%">
</p>

安装完成后点击「创建虚拟环境」，为本项目创建独立环境，例如命名为 `gemini_image_webapp`。虚拟环境能避免不同项目的 Python 包互相冲突。

<p align="center">
  <img src="Display pictures/BT/创建虚拟环境界面.png" alt="宝塔创建 Python 虚拟环境" width="80%">
</p>

#### 3. 上传或拉取项目

可在宝塔「文件」中把项目上传到 `/www/wwwroot/gemini-image-webapp`，也可以打开宝塔终端执行：

```bash
cd /www/wwwroot
git clone https://github.com/gbmomo/gemini-image-webapp.git
cd gemini-image-webapp
```

不要上传本地 `.env`、开发数据库或测试数据到公共仓库。通过宝塔上传旧数据时，确认 `www` 运行用户可以写入 `data/`、`static/images/` 和 `static/thumbnails/`；不要为了省事设置 `chmod -R 777`。

#### 4. 添加 Python 项目

在「Python 项目」页面点击「添加项目」，按下表填写：

| 配置项 | 推荐填写 |
|---|---|
| 项目名称 | `gemini-image-webapp` |
| Python 环境 | 上一步创建的虚拟环境 |
| 启动方式 | 命令行启动或 Gunicorn |
| 项目路径 | `/www/wwwroot/gemini-image-webapp` |
| 启动命令 | `gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 --timeout 360 app:app` |
| 环境变量 | 选择「指定变量」 |
| 启动用户 | `www` |
| 安装依赖 | `/www/wwwroot/gemini-image-webapp/requirements.txt` |

<p align="center">
  <img src="Display pictures/BT/宝塔面板添加python项目.png" alt="宝塔添加 Python 项目" width="80%">
</p>

上图已更新为当前推荐配置。请重点核对启动命令包含 `-w 1 --threads 8 -b 127.0.0.1:5000 --timeout 360`，并确认 Python 环境、项目路径和 `requirements.txt` 路径都属于同一个项目。

如果宝塔没有自动安装依赖，可在已经激活该虚拟环境的终端中执行：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### 5. 配置生产环境变量

先在已安装项目依赖的虚拟环境或自己的电脑上生成两个不同的随机密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

然后在宝塔项目的「环境变量」中选择「指定变量」，逐行填写：

```env
SECRET_KEY=第一个命令生成的随机值
ADMIN_PASSWORD=至少12位且包含大小写字母数字或符号中的三类
CREDENTIAL_ENCRYPTION_KEY=第二个命令生成的Fernet密钥
FLASK_ENV=production
FLASK_DEBUG=False
TRUST_PROXY_COUNT=1
```

API 配置有两种方式，二选一即可：

- 推荐：项目启动后使用 `admin` 登录，在管理后台保存 API Key 和自定义端点；敏感字段会加密存入数据库。
- 或者：继续在宝塔环境变量中增加 `GEMINI_API_KEY=你的Key`，使用自定义服务时再增加 `GEMINI_API_BASE_URL=https://你的兼容端点`。

需要邮件验证码注册时，再配置：

```env
EMAIL_SENDER=发件邮箱
EMAIL_PASSWORD=SMTP密码或授权码
SMTP_SERVER=SMTP服务器
SMTP_PORT=465
```

<p align="center">
  <img src="Display pictures/BT/环境变量配置界面.png" alt="宝塔 Python 项目环境变量配置" width="80%">
</p>

上图中的密钥内容已特意打码。保存前请确认环境变量列表中包含 `SECRET_KEY`、`ADMIN_PASSWORD`、`CREDENTIAL_ENCRYPTION_KEY`、`FLASK_ENV=production`、`FLASK_DEBUG=False` 和 `TRUST_PROXY_COUNT=1`；不要公开包含真实密钥的截图。

密钥注意事项：

- 不要直接使用 `.env.example` 中的示例值，也不要把密钥发到聊天、Issue 或截图中。
- `SECRET_KEY` 变更会让已有登录会话失效。
- `CREDENTIAL_ENCRYPTION_KEY` 必须长期保存；使用同一数据库时不能随意更换。建议把它与数据库备份分开保存在密码管理器或云厂商密钥服务中。
- 标准 Fernet 密钥为 44 个字符并以 `=` 结尾；部分宝塔版本保存后会去掉这个 Base64 填充符。当前版本会在严格校验后自动补回，显示为 43 个字符也可以正常使用，但密钥主体不能缺失或改变。
- 修改任何环境变量后都要重启项目。

#### 6. 启动并检查运行状态

点击「启动」或「重启」，确认项目状态为「运行中」，然后查看「项目日志」是否存在依赖缺失、端口占用或密钥错误。

<p align="center">
  <img src="Display pictures/BT/项目运行状态.png" alt="宝塔 Python 项目运行状态" width="80%">
</p>

可以在服务器终端执行以下命令检查本机服务：

```bash
curl -I http://127.0.0.1:5000/
```

此时不要开放安全组或宝塔防火墙的 5000 端口；下一步通过 Nginx 对外提供访问。

#### 7. 绑定域名并开启外网映射

进入项目设置的「域名管理」，添加已经解析到服务器的域名。通常使用 80 端口即可，HTTPS 会在下一步配置。

<p align="center">
  <img src="Display pictures/BT/域名绑定界面.png" alt="宝塔 Python 项目绑定域名" width="80%">
</p>

进入「外网映射」，开启代理并填写：

| 配置项 | 值 |
|---|---|
| 代理路由 | `/` |
| 代理端口 | `5000` |

<p align="center">
  <img src="Display pictures/BT/外网映射配置.png" alt="宝塔 Python 项目外网映射" width="80%">
</p>

宝塔会生成 Nginx 反向代理。确认代理目标是 `http://127.0.0.1:5000`，而不是把 Gunicorn 端口直接暴露到公网。

#### 8. 申请 SSL 并强制 HTTPS

进入该项目或对应网站的「SSL」页面，使用 Let's Encrypt、宝塔免费证书或自己的证书。签发成功后开启「强制 HTTPS」。

<p align="center">
  <img src="Display pictures/BT/SSL证书申请.png" alt="宝塔申请 SSL 证书" width="80%">
</p>

证书申请失败时，先检查域名解析是否已生效、80 端口是否开放，以及域名是否被其他站点占用。

#### 9. 调整 Nginx 上传与超时

在项目对应网站的「配置文件」中确认反向代理包含以下关键设置。宝塔已经生成的 SSL 证书路径和其他配置不要删除，只需合并缺少的内容：

```nginx
client_max_body_size 50m;

location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 360s;
    proxy_read_timeout 360s;
}
```

与宝塔自动生成的完整配置合并时，请按以下原则取舍：

- 保留宝塔管理的证书路径、`/.well-known/` 证书验证、访问日志和错误日志，不要把示例路径覆盖到自己的服务器。
- 本机 Gunicorn 的连接建立超时使用 `proxy_connect_timeout 60s`；上传和等待生图响应使用 `proxy_send_timeout 360s`、`proxy_read_timeout 360s`。Nginx 官方说明连接建立超时通常无法超过 75 秒，因此没有必要把 `proxy_connect_timeout` 设为 360 秒。
- 本项目不依赖 WebSocket，删除 `proxy_set_header Upgrade $http_upgrade` 和 `proxy_set_header Connection "upgrade"`；也不需要非标准的 `REMOTE-HOST` 请求头。
- `X-Forwarded-Host` 应使用 `$host`，这样同一个站点绑定多个域名时不会总是传递 `server_name` 中的第一个域名。
- 不要为登录、API、管理后台和用户图片启用 Nginx 代理缓存。若模板生成了 `location ~ /purge`、`proxy_cache_purge` 或 `add_header X-Cache`，而你没有明确配置缓存，请删除这些残留项。
- 如果在 `server` 层设置了 HSTS、`X-Frame-Options` 等 `add_header`，不要只在 `location /` 内单独增加一个 `add_header X-Cache`。传统 Nginx 继承规则是：当前层只要定义了任意 `add_header`，上层的全部 `add_header` 就不会自动继承。详见 [Nginx `add_header` 文档](https://nginx.org/en/docs/http/ngx_http_headers_module.html)。
- `/health` 中直接 `return 200` 只能证明 Nginx 正常，不能证明 Gunicorn、数据库或上游 API 正常；可用于 Nginx 存活检查，不应当作完整应用健康检查。
- HTTP/3/QUIC 与应用功能无关，是否启用交给宝塔和当前 Nginx 版本管理。启用时需要开放 UDP 443，并确保所有 `server_name` 域名都包含在证书中。不要把其他服务器的 `Alt-Svc` 草稿协议列表直接复制过来；可参考 [Nginx HTTP/3 文档](https://nginx.org/en/docs/http/ngx_http_v3_module.html)。

保存前使用宝塔的配置检查功能或执行 `nginx -t`，确认无误后再重载 Nginx。

<details>
<summary>展开查看可复制的宝塔 Nginx 完整模板</summary>

下面模板中的 `example.com`、`PROJECT_NAME` 和 `PROJECT_ROOT` 必须替换为自己的域名、宝塔项目名和项目绝对路径。宝塔自动生成的证书申请、扩展和监控日志配置可按面板实际内容保留。

```nginx
server
{
    listen 80;
    listen 443 ssl;
    listen 443 quic;
    http2 on;
    server_name example.com www.example.com;
    index index.html index.htm default.htm default.html;
    root PROJECT_ROOT;
    server_tokens off;

    include /www/server/panel/vhost/nginx/extension/PROJECT_NAME/*.conf;

    #CERT-APPLY-CHECK--START
    include /www/server/panel/vhost/nginx/well-known/PROJECT_NAME.conf;
    #CERT-APPLY-CHECK--END

    #SSL-START SSL相关配置
    #error_page 404/404.html;
    ssl_certificate /www/server/panel/vhost/cert/PROJECT_NAME/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/PROJECT_NAME/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:!MD5:!3DES;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Alt-Svc 'h3=":443"; ma=86400' always;
    error_page 497 https://$host$request_uri;
    #SSL-END

    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    client_max_body_size 50M;

    if ($scheme = http) {
        return 301 https://$host$request_uri;
    }

    #ERROR-PAGE-START  错误页相关配置
    #error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END

    #REWRITE-START  伪静态相关配置
    include /www/server/panel/vhost/rewrite/python_PROJECT_NAME.conf;
    #REWRITE-END

    location ~* (^|/)(\.env.*|\.user\.ini|\.htaccess|\.htpasswd|\.gitignore|\.gitattributes|LICENSE|README.*\.md|requirements\.txt|Dockerfile|docker-compose\.yml|pyproject\.toml|.*\.(py|pyc|pyo|db|sqlite|sqlite3|sql|log|bak|old|tmp))$
    {
        return 404;
    }

    location ~* ^/(data|tests|\.git|\.svn|\.vscode|\.idea|\.ssh|\.github|\.cache|\.venv|venv|__pycache__|node_modules|runtime)(/|$)
    {
        return 404;
    }

    location /.well-known/ {
        root /www/wwwroot/java_node_ssl;
    }

    if ($uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$") {
        return 403;
    }

    location = /health {
        access_log off;
        default_type text/plain;
        return 200 "OK\n";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_hide_header Strict-Transport-Security;
        proxy_hide_header X-Frame-Options;
        proxy_hide_header X-Content-Type-Options;
        proxy_hide_header X-XSS-Protection;
        proxy_hide_header Referrer-Policy;

        proxy_connect_timeout 60s;
        proxy_send_timeout 360s;
        proxy_read_timeout 360s;
    }

    access_log /www/wwwlogs/PROJECT_NAME.log;
    error_log /www/wwwlogs/PROJECT_NAME.error.log;
}
```

</details>

#### 10. 最终检查与备份

依次验证：

1. 使用 `https://你的域名` 打开网站，确认没有重定向循环且浏览器证书正常。
2. 使用 `admin` 和 `ADMIN_PASSWORD` 登录。
3. 在管理后台保存 API 配置并生成一张测试图片。
4. 如果配置了 SMTP，注册一个测试账号并检查验证码邮件。
5. 确认普通用户无法访问其他用户的原图和缩略图。

日常备份至少应包含：

- `data/users.db`
- `data/sessions/`
- `static/images/`
- `static/thumbnails/`

`CREDENTIAL_ENCRYPTION_KEY` 也必须备份，但不要和数据库放在同一个公开下载包中。恢复时需要同时恢复数据库、文件目录和原加密密钥。

#### 宝塔常见问题

**项目启动失败**：先查看项目日志。常见原因是依赖没有安装、环境变量缺失、项目路径错误、端口 5000 已被其他进程占用，或者 `CREDENTIAL_ENCRYPTION_KEY` 与已有数据库不匹配。

**访问域名出现 502**：确认 Python 项目处于运行中、Gunicorn 监听 `127.0.0.1:5000`，并确认 Nginx 的 `proxy_pass` 端口一致。

**不断跳转或提示 HTTPS 错误**：确认环境变量为 `TRUST_PROXY_COUNT=1`，Nginx 设置了 `X-Forwarded-Proto $scheme`，并且只有一层可信反向代理。若实际使用 Cloudflare 加 Nginx，应根据真实代理链重新评估该值，不能盲目增加。

**上传提示 413**：确认 Nginx 的 `client_max_body_size` 不小于应用的 `MAX_REQUEST_BYTES`。

**生成经常超时**：Gunicorn 和 Nginx 的超时都应至少为 360 秒，同时检查上游 API 是否可访问。

**数据库凭据无法解密**：恢复部署时使用了错误的 `CREDENTIAL_ENCRYPTION_KEY`。不要反复生成新值覆盖旧值，应找回与该数据库配套的原密钥。

**宝塔保存后 Fernet 密钥末尾的 `=` 消失**：末尾的 `=` 是 Base64 填充符，当前版本兼容宝塔保存的 43 字符无填充形式。确认其他字符没有改变后重启项目即可；旧版本代码需要先更新。

### worker 和 Redis 怎么选

推荐命令中的 `-w 1 --threads 8` 已适合个人站点和中小流量服务，而且不需要 Redis。只有在监控确认单 worker 已成为瓶颈，并准备启动 `-w 2`、`-w 4`、多台服务器或多个容器实例时，才需要让所有进程共享限流计数：

```env
RATELIMIT_STORAGE_URI=redis://127.0.0.1:6379/0
```

Redis 应只监听本机或可信内网，绝不能把 6379 端口直接开放到公网。增加 worker 之前还应测试 SQLite 写入、会话文件锁、内存占用和上游 API 配额；worker 越多并不一定越快。

### 手动使用 Gunicorn + Nginx

不使用宝塔时也可以按相同结构部署。单层 Nginx 反向代理需要设置 `FLASK_ENV=production`、`FLASK_DEBUG=False`、`TRUST_PROXY_COUNT=1`，并使用上文的 Gunicorn 与 Nginx 配置。

`TRUST_PROXY_COUNT` 必须等于真实可信代理层数；应用直接对外监听时不要启用。确保服务账号只能按需读取源码和环境变量，并能写入数据库、`DATA_DIR`、`IMAGES_DIR` 和 `THUMBNAILS_DIR`。

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

主要 JSON 写入字段如下：登录为 `username`、`password`；发验证码为 `email`；注册为 `username`、`email`、`password`、`verification_code`；修改标题为 `title`；生成图片为 `session_id`、`prompt`、`model`、`thinking_level`、`image_size`、`aspect_ratio`、`reference_images`；兑换为 `code`；管理员点数调整为 `amount`；清理为 `cutoff_date`；生成卡密为 `credits`、`count`；API/SMTP 设置为 `provider`、`api_key`、`custom_base_url`、`default_model`、`email_sender`、`email_password`、`smtp_server`、`smtp_port`；模型定价为 `prices` 数组，其中每项包含 `model_id`、`image_size`、`credits`。

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
