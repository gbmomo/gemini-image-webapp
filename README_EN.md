# Gemini Nano Banana AI Image Generation Website

<p align="center">
  <a href="README.md">简体中文</a> | <b>English</b>
</p>

<p align="center">
  <img src="static/logo.ico" alt="Logo" width="120" height="120">
</p>

<p align="center">
  A self-hosted image generation website built with Flask and Gemini image models, including users, credits, conversations, redemption codes, and an admin dashboard.
</p>

<p align="center">
  <a href="https://nano.gitsay.com/">Live demo</a> ·
  <a href="https://github.com/gbmomo/gemini-image-webapp">Repository</a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/gbmomo/gemini-image-webapp?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/gbmomo/gemini-image-webapp?style=flat-square" alt="Forks">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg" alt="License">
</p>

> This project is licensed under [CC BY-NC-SA 4.0](LICENSE). You must credit [@gbmomo](https://github.com/gbmomo), link to the [original project](https://github.com/gbmomo/gemini-image-webapp), refrain from commercial use without separate permission, and distribute adaptations under the same license. Commercial licensing: S@gitsay.com, QQ: 550948321, WeChat: Goblin_MoMo.

## Quick Navigation

[Features](#current-features) · [Quick start](#quick-start) · [Environment variables](#environment-variables) · [Production deployment](#production-deployment) · [Security boundaries](#storage-and-security-boundaries) · [Troubleshooting](#troubleshooting)

## Current Features

- Text-to-image, reference-image generation, and contextual multi-turn image iteration. References can be added with the file picker, drag and drop, or paste.
- Visitors may browse the full home page, enter a prompt, and choose generation settings without signing in. Creating a conversation, adding references, or generating requires authentication; the guest draft is restored after login without automatically generating or charging credits.
- Each user can create, switch, and delete conversations. The first successful prompt supplies the first 20 characters of the automatic title and locks the model, resolution, and ratio; changing them requires a new conversation. A title-update API exists, but the current UI has no rename control.
- Chinese and English switching. Set the default with `DEFAULT_LANG` in `static/js/i18n.js`.
- Email-code registration, username/password login, logout, and signed-cookie login sessions.
- New users receive 4 credits. Regular users are charged by model and resolution; administrators generate without charge.
- Self-service redemption codes, plus admin-side batch generation and usage history.
- Admin management for users, roles, credits, conversations, messages, API/SMTP settings, and model pricing.
- Historical-data cleanup, orphan-image cleanup, thumbnails, file locking, and generation-charge recovery.
- CSRF protection, brute-force rate limits, upload validation, media ownership checks, and production HTTPS/security headers.
- Click-to-preview and download for generated images, `Ctrl+Enter` submission, and a conversation sidebar adapted for narrow screens.

Registration requires a unique username of 3 to 64 characters, a unique email no longer than 254 characters, and a password of 6 to 256 characters containing both letters and digits. The six-digit verification code expires after ten minutes and can be used only once.

## Model Capabilities

The backend validates each model's thinking levels, resolutions, aspect ratios, and reference-image count. These are not merely UI restrictions. Thinking level is locked with the other generation settings after the first successful image.

| Model ID | Display name | Resolutions | Thinking levels | Max references | Aspect ratios |
|---|---|---:|---|---:|---|
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | 1K | `minimal`, `high` | 14 | Common ratios |
| `gemini-3.1-flash-image` | Nano Banana 2 | 512, 1K, 2K, 4K | `minimal`, `high` | 14 | Common ratios plus 1:4, 1:8, 4:1, and 8:1 |
| `gemini-3-pro-image` | Nano Banana Pro | 1K, 2K, 4K | Automatic, not adjustable | 14 | Common ratios |
| `gemini-2.5-flash-image` | Nano Banana | 1K | Not adjustable | 3 | Common ratios |

Common ratios are `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, and `21:9`.

In the current UI, a new conversation starts with the admin-selected default model, `1K`, and `1:1`. The `auto` ratio remains only for compatibility with historical conversations.

Reference images may be PNG, JPEG, GIF, WEBP, or ICO. Default limits are 10 MiB per image, 35 MiB total per request, and 40 million pixels per image. Prompts may contain up to 100,000 characters. The byte and pixel limits are configurable through environment variables. If an API response contains multiple images, the current implementation keeps only the first, stores it as PNG, and creates a JPEG thumbnail.

## Credits and Charging

The following defaults apply until an administrator saves custom prices:

| Resolution | Default credits |
|---|---:|
| 512 | 1 |
| 1K | 1 |
| 2K | 2 |
| 4K | 4 |

Administrators can set a separate price from `0` to `100000` credits for every supported model/resolution pair. A zero price makes that combination free for regular users.

For a regular user, credits are atomically reserved before generation. The charge is committed only after an image is generated and persisted in the conversation. API failures, text-only or empty responses, and persistence failures trigger a refund and remove files created by that attempt. A persistent charge ledger reconciles expired reservations left by a crashed process. A cross-process file lock serializes generations within the same conversation so history cannot be overwritten by concurrent requests.

## Quick Start

Python 3.10 or newer is required.

```bash
git clone https://github.com/gbmomo/gemini-image-webapp.git
cd gemini-image-webapp

python -m venv .venv
```

Activate the environment and install dependencies:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy the configuration template:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Set at least these values when using dashboard-managed credentials:

```env
SECRET_KEY=replace_with_a_strong_random_value
ADMIN_PASSWORD=replace_with_the_admin_password
CREDENTIAL_ENCRYPTION_KEY=replace_with_an_independent_fernet_key
```

Generate a `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate the independent database credential encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Start the app:

```bash
python app.py
```

Open `http://127.0.0.1:5000`, sign in as `admin` with `ADMIN_PASSWORD`, then configure Gemini API and SMTP settings in the admin dashboard. You may instead set `GEMINI_API_KEY` and the email settings in `.env`.

At startup, `ADMIN_PASSWORD` is synchronized to the existing `admin` account. The application refuses to start when it is missing. Production passwords must contain at least 12 characters and three character classes.

## Environment Variables

API settings saved in the admin dashboard take precedence as a group over `GEMINI_*` environment variables, and the saved default model takes precedence over `DEFAULT_MODEL`. The SMTP sender, password, server, and port are each resolved independently from a non-empty database value and then their environment fallback. See [.env.example](.env.example) for the complete template.

### Core and API

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | none | Flask Session and CSRF signing key; required |
| `ADMIN_PASSWORD` | none | Password for the `admin` account; required; production requires 12 characters and three character classes |
| `CREDENTIAL_ENCRYPTION_KEY` | none | Independent Fernet key required when API/SMTP credentials are stored from the dashboard |
| `GEMINI_API_KEY` | empty | Gemini API key; may instead be saved in the admin dashboard |
| `GEMINI_API_BASE_URL` | empty | Custom compatible endpoint; enables the `custom` provider in environment mode |
| `DEFAULT_MODEL` | `gemini-3.1-flash-image` | Default model; must be one of the model IDs above |
| `FLASK_ENV` | `development` | `production` forces HTTPS and enables production security headers |
| `FLASK_DEBUG` | `False` | Flask debug mode; keep disabled in production |

### Email

| Variable | Default | Description |
|---|---|---|
| `EMAIL_SENDER` | empty | SMTP sender/login account |
| `EMAIL_PASSWORD` | empty | SMTP password or app password |
| `SMTP_SERVER` | empty | SMTP server |
| `SMTP_PORT` | `465` | SMTP-over-SSL port |
| `SMTP_TIMEOUT` | `15` | SMTP connection timeout in seconds |

### Deployment, Storage, and Limits

| Variable | Default | Description |
|---|---|---|
| `TRUST_PROXY_COUNT` | `0` | Number of trusted reverse proxies; usually `1` behind one Nginx layer |
| `RATELIMIT_STORAGE_URI` | `memory://` | Rate-limit store; multiple workers require a shared backend such as Redis |
| `DATABASE_FILE` | `data/users.db` | SQLite file path |
| `DATA_DIR` | `data` | Conversation JSON and lock-file directory |
| `IMAGES_DIR` | `static/images` | Generated and reference image directory |
| `THUMBNAILS_DIR` | `static/thumbnails` | Thumbnail directory |
| `DATABASE_BUSY_TIMEOUT_MS` | `5000` | SQLite busy timeout in milliseconds |
| `MAX_REQUEST_BYTES` | `52428800` | HTTP request limit, 50 MiB by default |
| `MAX_REFERENCE_IMAGE_BYTES` | `10485760` | Per-reference limit, 10 MiB by default |
| `MAX_REFERENCE_TOTAL_BYTES` | `36700160` | Total reference limit per request, 35 MiB by default |
| `MAX_REFERENCE_PIXELS` | `40000000` | Maximum pixels per reference image |
| `GENERATION_CHARGE_TTL_SECONDS` | `900` | Recovery window for pending charges; code enforces at least 600 seconds |
| `GENERATION_LOCK_TIMEOUT` | `330` | Wait time for the per-conversation generation lock, in seconds |
| `DISABLE_BACKGROUND_TASKS` | `false` | `true` disables the in-app cleanup thread |
| `CHAT_IDLE_TIMEOUT` | `1800` | In-process Gemini chat-cache idle time, in seconds |
| `CHAT_CLEANUP_INTERVAL` | `600` | Background cleanup interval, in seconds |

`DATA_DIR` controls only the conversation directory and maintenance-lock location. The independent `DATABASE_FILE` setting always controls the SQLite path.

## Admin Dashboard

Administrators can open `/admin` to:

- View users, roles, balances, conversation counts, and message counts, including conversation and message details for a selected user.
- Add or subtract user credits, provided the resulting balance is not negative.
- Grant or revoke administrator access. The primary `admin` account's role cannot be changed.
- Delete regular users and their conversations and associated images. Administrator accounts cannot be deleted.
- Generate 1 to 100 redemption codes per batch, each worth more than zero credits. Full codes are returned only once; later views show only prefixes and usage records.
- Remove messages before a selected date, empty conversations, associated files, and orphaned files, or clear all conversation data.
- Switch between Google AI Studio and custom-URL providers and set the API key, custom URL, and default model.
- Configure the sender address, SMTP password, server, and port.
- Edit prices by model and resolution. Saving settings rebuilds the current process's client immediately; other workers detect the settings version and refresh automatically.

The current recharge dialog's “Buy now” button is hard-coded to `https://pay.ldxp.cn/shop/momo/fhrvq4`. Self-hosted operators should replace it in `templates/index.html` with their own purchase URL or remove the button. Code redemption itself is local. The “from `$0.04/image`” banner is also fixed copy in `static/js/i18n.js`; it does not follow admin-configured credit prices.

## Storage and Security Boundaries

| Data | Location | Actual protection |
|---|---|---|
| Users, codes, API/SMTP settings, prices, charge ledger | SQLite, `data/users.db` by default | Passwords and verification codes use salted hashes; redemption codes store a verification hash, SHA-256 lookup value, and prefix; API keys and SMTP passwords use Fernet encryption |
| Conversations and messages | `data/sessions/user_<id>.json` | Plain local JSON with file locks, temporary files, `fsync`, and atomic replacement |
| Generated images, references, thumbnails | `static/images`, `static/thumbnails` | Plain local files; HTTP access is limited to the file owner or an administrator |

Important boundaries:

- API keys and SMTP passwords are encrypted with `CREDENTIAL_ENCRYPTION_KEY`; keep that key separate from the database and its backups. Emails, conversation JSON, and images still depend on host permissions, disk encryption, and backup policy.
- Flask's Session cookie is signed, not a database/file encryption mechanism. Do not treat `SECRET_KEY` as an at-rest encryption key.
- Saving API/SMTP settings retains only the current row. The first upgraded startup encrypts the active row, removes historical settings, and rewrites SQLite pages. Rotate credentials that were previously stored in plaintext and remove old backups.
- During generation, prompts, conversation context, and reference images are sent to the configured Gemini/API provider. Registration sends the recipient email and code to the configured SMTP service. Operators must disclose data processing according to the providers they use.
- Back up the SQLite database, `data/sessions`, images, and thumbnails. A database-only backup cannot restore complete history.

The application also validates CSRF on all unsafe HTTP methods with a one-hour token lifetime; sets Session cookies to `HttpOnly`, `SameSite=Lax`, and `Secure` in production; limits login to `5/minute`, verification codes to `1/minute`, registration to `3/hour`, generation to `20/hour`, and all routes by default to `100/hour` and `1000/day`, keyed by client IP; and validates upload Base64 data, format, byte size, and pixel count.

## Production Deployment

The recommended topology is HTTPS client → Nginx → Gunicorn on `127.0.0.1:5000`. Do not expose the Flask development server or Gunicorn port 5000 directly to the internet.

For a personal or small-to-medium deployment, start with one worker and multiple threads:

```bash
gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 --timeout 360 app:app
```

- `-w 1` runs one application process, so the default in-memory rate limiter remains consistent and Redis is not required.
- `--threads 8` allows that process to wait on several network requests concurrently; it does not limit the site to one user.
- `--timeout 360` accommodates image generation. Set the reverse proxy send and read timeouts to the same value.

Set the following production variables before starting the service:

```env
SECRET_KEY=a_unique_random_value_of_at_least_32_bytes
ADMIN_PASSWORD=a_password_of_at_least_12_characters_and_3_character_classes
CREDENTIAL_ENCRYPTION_KEY=a_separately_generated_fernet_key
FLASK_ENV=production
FLASK_DEBUG=False
TRUST_PROXY_COUNT=1
```

Generate the two keys independently:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

When restoring or moving an existing database, preserve its original `CREDENTIAL_ENCRYPTION_KEY`. Replacing that key makes the encrypted API and SMTP credentials unreadable. Changing `SECRET_KEY` invalidates existing browser sessions.

A standard Fernet key contains 44 characters and ends with `=`. Some hosting panels remove that Base64 padding when saving environment variables. This version strictly validates the remaining 43 characters and restores the omitted padding automatically; no other character may be removed or changed.

Key settings for one trusted Nginx proxy layer are:

```nginx
server {
    listen 443 ssl;
    server_name example.com;

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
}
```

When merging this block into a panel-generated Nginx configuration:

- Preserve panel-managed certificate paths, ACME `/.well-known/` rules, and log destinations. Do not replace them with paths from an example.
- Use `proxy_connect_timeout 60s` for the local Gunicorn connection and `proxy_send_timeout 360s` plus `proxy_read_timeout 360s` for uploads and image-generation responses. Nginx documents that connection establishment timeouts usually cannot exceed 75 seconds, so a 360-second connect timeout is not useful.
- The application does not use WebSockets. Remove `Upgrade`/`Connection: upgrade` and non-standard `REMOTE-HOST` request headers.
- Use `$host` for `X-Forwarded-Host`, especially when one server block accepts more than one hostname.
- Do not enable proxy caching for authenticated pages, `/api/`, `/admin`, or user media. Remove unused `proxy_cache_purge`, public `/purge` locations, and `X-Cache` headers generated by cache templates.
- Under the traditional Nginx inheritance rule, defining any `add_header` inside `location /` prevents server-level security headers from being inherited there. Avoid a location-only `add_header X-Cache`, or deliberately repeat/merge every required header. See the official [Nginx header module documentation](https://nginx.org/en/docs/http/ngx_http_headers_module.html).
- A static `location /health { return 200; }` checks Nginx only, not Gunicorn, the database, or the upstream API.
- HTTP/3 is optional and version-dependent. If the panel enables it, open UDP 443, ensure the certificate covers every `server_name`, and follow the current [Nginx HTTP/3 documentation](https://nginx.org/en/docs/http/ngx_http_v3_module.html) instead of copying old draft `Alt-Svc` tokens.

Run `nginx -t` or the panel's configuration checker before every reload. Keep port 5000 closed to the public internet and expose only Nginx ports 80/443. `TRUST_PROXY_COUNT` must match the actual trusted proxy chain; do not increase it blindly.

### Workers and Redis

Keep `-w 1 --threads 8` unless monitoring shows that one process is a bottleneck. Use a shared rate-limit backend before running multiple workers, containers, or server instances:

```env
RATELIMIT_STORAGE_URI=redis://127.0.0.1:6379/0
```

Redis must remain on localhost or a trusted private network; never expose port 6379 publicly. More workers also increase SQLite write contention, file-lock activity, memory use, and upstream API concurrency, so scale based on measurements rather than a generic CPU formula.

### Deployment Checklist

1. Confirm that the service account can write to the database, `DATA_DIR`, `IMAGES_DIR`, and `THUMBNAILS_DIR`, without granting world-writable permissions.
2. Configure the API in the admin dashboard or set `GEMINI_API_KEY`; add SMTP variables only when email registration is needed.
3. Enable a valid TLS certificate and force HTTPS.
4. Set `client_max_body_size 50m` and 360-second proxy timeouts.
5. Test admin login, one image generation, email verification if enabled, and cross-user media access controls.
6. Back up `data/users.db`, `data/sessions/`, `static/images/`, and `static/thumbnails/`. Store `CREDENTIAL_ENCRYPTION_KEY` separately from database backups.

The Chinese README includes a screenshot-based [BT Panel deployment guide](README.md#宝塔面板部署新手推荐).

## HTTP Route Overview

Every `POST`, `PUT`, and `DELETE` request requires a valid CSRF token. The web UI reads it from `<meta name="csrf-token">` and sends it as `X-CSRFToken`. Direct API clients must retain the same browser Session cookie and token.

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/` | Public | Main page and CSRF Session initialization |
| GET | `/login` | Public | Redirect to the main page |
| GET | `/api/models` | Public | Model capabilities, prices, and default model |
| POST | `/api/login` | Public | Sign in |
| POST | `/api/send-verification-code` | Public | Send a registration code |
| POST | `/api/register` | Public | Register a user |
| POST | `/api/logout` | Signed in | Sign out and return a 302 page redirect |
| GET / POST | `/api/sessions` | Signed in | List or create conversations |
| GET / DELETE | `/api/sessions/<session_id>` | Signed in | Get or delete a conversation |
| PUT | `/api/sessions/<session_id>/title` | Signed in | Rename a conversation |
| POST | `/api/generate` | Signed in | Generate or iterate an image |
| POST | `/api/redeem` | Signed in | Redeem a code |
| GET | `/static/images/<filename>` | File owner or administrator | Fetch a generated/reference image |
| GET | `/static/thumbnails/<filename>` | File owner or administrator | Fetch a thumbnail |
| GET | `/admin` | Administrator | Admin dashboard page |
| GET | `/api/admin/users` | Administrator | User and statistics list |
| DELETE | `/api/admin/users/<id>` | Administrator | Delete a regular user |
| POST | `/api/admin/users/<id>/toggle-admin` | Administrator | Toggle a role |
| POST | `/api/admin/users/<id>/credits` | Administrator | Add or subtract credits |
| GET | `/api/admin/users/<id>/sessions` | Administrator | View a user's conversations |
| GET | `/api/admin/users/<id>/sessions/<session_id>` | Administrator | View message details |
| POST | `/api/admin/cleanup` | Administrator | Clean historical data and orphaned files |
| GET / POST | `/api/admin/card-keys` | Administrator | List or generate redemption codes |
| GET / POST | `/api/admin/api-settings` | Administrator | Read or save API/SMTP settings |
| GET / PUT | `/api/admin/model-pricing` | Administrator | Read or save model pricing |

The main JSON write fields are: `username` and `password` for login; `email` for sending a code; `username`, `email`, `password`, and `verification_code` for registration; `title` for renaming; `session_id`, `prompt`, `model`, `thinking_level`, `image_size`, `aspect_ratio`, and `reference_images` for generation; `code` for redemption; `amount` for admin credit changes; `cutoff_date` for cleanup; `credits` and `count` for code generation; `provider`, `api_key`, `custom_base_url`, `default_model`, `email_sender`, `email_password`, `smtp_server`, and `smtp_port` for API/SMTP settings; and a `prices` array of `model_id`, `image_size`, and `credits` objects for model pricing.

## Project Layout

```text
app.py                 Flask app, routes, generation, and conversation logic
database.py            SQLite initialization, migrations, users, codes, pricing, and charges
email_service.py       SMTP verification email
templates/             Main and admin templates
static/js/             Authentication, generation, admin, modal, and i18n code
static/css/            Stylesheets
data/                   SQLite, conversation JSON, and locks (created at runtime)
static/images/          Generated and reference images (created at runtime)
static/thumbnails/      Thumbnails (created at runtime)
tests/                  unittest regression tests
Display pictures/       README screenshots
```

## Tests

The tests use isolated temporary databases and storage directories; do not point them at the real `data/users.db`:

```bash
python -m unittest discover -v
```

## Screenshots

<p align="center">
  <img src="Display pictures/EN/登录界面.png" alt="Login" width="45%">
  <img src="Display pictures/EN/注册页面.png" alt="Registration" width="45%">
</p>

<p align="center">
  <img src="Display pictures/EN/网站首页（生成图片的效果）.png" alt="Image generation" width="80%">
</p>

<p align="center">
  <img src="Display pictures/EN/管理员后台首页.png" alt="Admin dashboard" width="80%">
</p>

## Troubleshooting

**“API is not configured”**: Sign in as `admin` and save an API key in the dashboard, or set `GEMINI_API_KEY` and restart.

**Registration email cannot be sent**: Configure the sender account, password/app password, SMTP server, and port. The current mail client uses SMTP over SSL.

**“Page verification has expired”**: Refresh the page and retry. Ensure the request retains cookies and sends the current page's `X-CSRFToken`. Public write endpoints such as login and registration also require CSRF.

**Rate limits differ between workers**: Point `RATELIMIT_STORAGE_URI` to Redis shared by every worker, then restart all workers.

## License

[CC BY-NC-SA 4.0](LICENSE). Commercial use requires separate permission.
