# Jaikalki HRMS — Production Deployment Guide

This document covers deploying the API + admin web + Flutter mobile to
production. The recommended target is a single Linux host (Ubuntu 22.04+)
running Docker Compose, fronted by Nginx with Let's Encrypt TLS.

Domains used in this guide:

- API: `https://api-hrms.jaikalki.com`
- Admin web: `https://portal.jaikalki.com`

## 0. Prerequisites

- Ubuntu 22.04+ (4 vCPU / 8 GB RAM minimum for ~100 employees)
- Docker Engine + Docker Compose plugin
- Nginx
- Certbot (for Let's Encrypt)
- An email-sending option (SMTP or SES) — required for password resets

## 1. Clone + configure

```bash
sudo mkdir -p /opt/jaikalki && cd /opt/jaikalki
sudo chown $USER:$USER .
git clone https://github.com/jaikalkitechnology/harms_jaikalki.git hrms
cd hrms/hrms_backend
cp .env.production.example .env
$EDITOR .env
```

The minimum you must change in `.env`:

| Variable | Notes |
|---|---|
| `JWT_SECRET_KEY` | 64+ random chars. `openssl rand -base64 64` |
| `JUSTICE_ENCRYPTION_KEY` | 32 raw bytes, base64-encoded. `openssl rand -base64 32` |
| `DATABASE_URL` / `_SYNC` | Point at managed MySQL or the bundled container |
| `PUBLIC_BASE_URL` | `https://api-hrms.jaikalki.com` |
| `CORS_ORIGINS` | `["https://portal.jaikalki.com"]` |
| `HRMS_UPLOADS_PATH` | Host directory for the uploads volume — e.g. `/srv/jaikalki/uploads` |

Then create the uploads directory:

```bash
sudo mkdir -p /srv/jaikalki/uploads
sudo chown -R 1000:1000 /srv/jaikalki/uploads
```

## 2. Bring up the stack

```bash
cd /opt/jaikalki/hrms/hrms_backend
docker compose --profile api up -d --build
```

Once MySQL is healthy, run the migrations + seed:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed_auth
docker compose exec api python -m scripts.seed_employees
```

Repeat the relevant seeders for each enabled module (see
`hrms_backend/scripts/seed_*.py`).

Verify:

```bash
curl -s http://localhost:8000/api/v1/health/ready | jq
```

You should see `{"status":"ok", "checks":{...}}` once DB + storage are up.

## 3. Build the admin web

```bash
cd /opt/jaikalki/hrms/hrms_admin_web
cp .env.production .env       # ensures VITE_API_BASE_URL points at api-hrms.jaikalki.com
npm ci
npm run build
sudo mkdir -p /var/www/portal.jaikalki.com
sudo cp -r dist/* /var/www/portal.jaikalki.com/
```

## 4. Nginx + TLS

`/etc/nginx/sites-available/api-hrms.jaikalki.com`:

```nginx
server {
    listen 80;
    server_name api-hrms.jaikalki.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api-hrms.jaikalki.com;

    # certbot will populate these
    ssl_certificate     /etc/letsencrypt/live/api-hrms.jaikalki.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-hrms.jaikalki.com/privkey.pem;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 25M;     # for selfies, evidence, payslips, etc.

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

`/etc/nginx/sites-available/portal.jaikalki.com`:

```nginx
server {
    listen 80;
    server_name portal.jaikalki.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name portal.jaikalki.com;
    ssl_certificate     /etc/letsencrypt/live/portal.jaikalki.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/portal.jaikalki.com/privkey.pem;

    root /var/www/portal.jaikalki.com;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Long-cache hashed assets
    location /assets/ {
        expires 1y;
        access_log off;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable + reload:

```bash
sudo ln -s /etc/nginx/sites-available/api-hrms.jaikalki.com /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/portal.jaikalki.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api-hrms.jaikalki.com -d portal.jaikalki.com
```

## 5. Health probes

```
GET /api/v1/health/live    →  200 always (liveness)
GET /api/v1/health/ready   →  200 with all checks green, 503 on DB/storage down
GET /api/v1/health         →  legacy single-status endpoint
```

Wire `/api/v1/health/ready` into your uptime monitor and your reverse
proxy / load-balancer health check.

## 6. Backups

The API container ships with two scripts under `scripts/ops/`:

- `backup_mysql.sh` — gzipped `mysqldump`, prunes after `RETAIN_DAYS`
- `restore_mysql.sh` — drops + restores from a backup file

Recommended cron on the host (root crontab):

```cron
30 2 * * * MYSQL_PASSWORD='Love1718' BACKUP_DIR=/srv/jaikalki/backups \
    /opt/jaikalki/hrms/hrms_backend/scripts/ops/backup_mysql.sh \
    >> /var/log/jaikalki-hrms-backup.log 2>&1
```

For the uploads directory, sync nightly to S3/Backblaze B2:

```cron
0 3 * * * /usr/local/bin/aws s3 sync /srv/jaikalki/uploads \
    s3://jaikalki-hrms-uploads/ --delete --quiet
```

## 7. Storage backend choice

The default is `STORAGE_BACKEND=local` which writes to
`/srv/jaikalki/uploads`. To switch to S3/MinIO:

```env
STORAGE_BACKEND=s3
S3_ENDPOINT=https://s3.ap-south-1.amazonaws.com
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=jaikalki-hrms-prod
S3_REGION=ap-south-1
```

No code changes required — the storage helper dispatches at runtime.

## 8. Mobile app builds

```bash
cd hrms_mobile
flutter pub get

# Android
flutter build apk --release \
    --dart-define=API_BASE_URL=https://api-hrms.jaikalki.com

# iOS (Mac with Xcode)
flutter build ios --release \
    --dart-define=API_BASE_URL=https://api-hrms.jaikalki.com
```

Android: signed AAB → Google Play console.
iOS: archive in Xcode → App Store Connect → TestFlight, then production.

## 9. Hardening checklist

The API ships with these defaults — verify they're enabled:

- [x] CORS restricted to `CORS_ORIGINS`
- [x] Security headers (HSTS, X-Frame-Options, X-Content-Type-Options,
      Referrer-Policy, Permissions-Policy) via `SecurityHeadersMiddleware`
- [x] In-process rate limiter on `/auth/*` and `/justice/submit`
- [x] AES-GCM-256 field encryption on Justice complaints
- [x] JWT access tokens (15m) + refresh rotation with `jti` revocation
- [x] httpOnly cookies + double-submit CSRF token for admin sessions
- [x] Geo-fence for attendance + field check-ins; mock-GPS rejected
- [x] Anti-cheating signals on exam attempts (auto-invalidate at 5 flags)

To do per-environment:

- [ ] Rotate `JWT_SECRET_KEY` and `JUSTICE_ENCRYPTION_KEY`
- [ ] Restrict MySQL bind to `127.0.0.1` (or move to managed RDS)
- [ ] Enable Redis password (`REDIS_URL=redis://:pwd@host:6379/0`)
- [ ] Configure UFW: allow 22, 80, 443; deny everything else
- [ ] Set up Cloudflare (optional) for DDoS protection + caching of
      `/uploads/*` if the local backend is exposed publicly
- [ ] Run an OWASP ZAP baseline scan against staging before launch

## 10. Deploying updates

```bash
cd /opt/jaikalki/hrms
git pull
cd hrms_backend
docker compose --profile api up -d --build
docker compose exec api alembic upgrade head
cd ../hrms_admin_web
npm ci && npm run build
sudo cp -r dist/* /var/www/portal.jaikalki.com/
```

Zero-downtime upgrades require a load balancer in front of two API
replicas; this single-host guide trades a few seconds of 502 during
restart for simplicity. Add `restart: unless-stopped` (already set) and
the API is back online within ~5 seconds.

## 11. Monitoring (recommended)

- Uptime: hit `/api/v1/health/ready` from BetterStack / Healthchecks.io
- Logs: `docker compose logs -f api` — pipe into Loki/CloudWatch in prod
- Errors: wire `sentry-sdk[fastapi]` to `SENTRY_DSN` if you use Sentry

## 12. CI/CD

`.github/workflows/` ships with three workflows:

- `backend-ci.yml` — pytest on every push touching `hrms_backend/`
- `admin-web-ci.yml` — `tsc --noEmit` + `npm run build` on `hrms_admin_web/`
- `mobile-ci.yml` — `flutter analyze` + `flutter test` on `hrms_mobile/`

Add a `deploy.yml` that SSHs into the server and runs the update steps
in §10 once you wire up the deploy SSH key as a repo secret.
