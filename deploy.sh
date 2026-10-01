#!/usr/bin/env bash
# ============================================================================
#  Kutubxona — serverga o'rnatish (Ubuntu / Debian)
#
#  Ishga tushirish:
#      curl -O https://raw.githubusercontent.com/UserMuhammadaziz/Kutubxona/main/deploy.sh
#      chmod +x deploy.sh
#      sudo ./deploy.sh
#
#  Domain:  kutubxona.sharqsoft.uz
#  GitHub:  https://github.com/UserMuhammadaziz/Kutubxona
#
#  Takroriy ishga tushirish ham mumkin — skript mavjud qismlarni
#  o'zgartirmaydi, faqat yetishmayotganini o'rnatadi.
# ============================================================================
set -euo pipefail

# ----------------------------- SOZLAMALAR -----------------------------------
DOMAIN="${DOMAIN:-kutubxona.sharqsoft.uz}"
REPO="${REPO:-https://github.com/UserMuhammadaziz/Kutubxona.git}"
BRANCH="${BRANCH:-main}"
APP_USER="${APP_USER:-kutubxonachi}"
APP_DIR="${APP_DIR:-/var/www/kutubxona}"
DB_NAME="${DB_NAME:-kutubxona}"
DB_USER="${DB_USER:-kutubxonachi}"
SERVICE_USER="${SERVICE_USER:-kutubxonachi}"

say()  { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[ohlap] %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[xato] %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "root bilan ishga tushiring:  sudo ./deploy.sh"

# --------------------------- 1. OS ANIQLASH ---------------------------------
say "1/11 Tizimni aniqlash"
[[ -r /etc/os-release ]] && . /etc/os-release
case "${ID:-} ${VERSION_ID:-}" in
  *ubuntu*|*debian*) : ;;
  *) warn "OS=${PRETTY_NAME:-noma'lum} — Ubuntu/Debian emas. Davom etilmoqda." ;;
esac
echo "    $PRETTY_NAME"

# --------------------------- 2. PAKETLAR ------------------------------------
say "2/11 Paketlar o'rnatilmoqda (bu 2-5 daqiqa davom etadi)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  git python3 python3-venv python3-pip \
  nginx postgresql postgresql-contrib \
  redis-server libpq-dev build-essential \
  ca-certificates curl ufw fail2ban

systemctl enable --now postgresql
systemctl enable --now redis-server
systemctl enable --now nginx

# --------------------------- 3. FOYDALANUVCHI --------------------------------
say "3/11 Foydalanuvchi va kod tayyorlanmoqda"
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "$SERVICE_USER"
fi

if [[ -d "$APP_DIR/.git" ]]; then
  say "    Kod yangilanmoqda (git pull)"
  sudo -u "$SERVICE_USER" git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  sudo -u "$SERVICE_USER" git clone --branch "$BRANCH" --depth 1 "$REPO" "$APP_DIR"
fi

# --------------------------- 4. PYTHON MUHIT ---------------------------------
say "4/11 Python virtual muhit"
sudo -u "$SERVICE_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/pip" install -q --upgrade pip wheel
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
echo "    $(sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/python" -c 'import django;print("Django",django.get_version())')"

# --------------------------- 5. POSTGRESQL ----------------------------------
say "5/11 PostgreSQL bazasi"

# .env allaqach bo'lsa, undagi parolni qayta ishlatamiz (takroriy o'rnatishda
# parol o'zgarmasligi kerak).
if [[ -f "$APP_DIR/.env" ]]; then
  DB_PASSWORD="$(grep -E '^DB_PASSWORD=' "$APP_DIR/.env" | head -n1 | cut -d= -f2- || true)"
fi
if [[ -z "${DB_PASSWORD:-}" ]]; then
  DB_PASSWORD="$(openssl rand -base64 32 | tr -d '/+=' | head -c 28)"
fi

sudo -u postgres psql -qc "DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$DB_USER') THEN
    CREATE ROLE \"$DB_USER\" LOGIN;
  END IF;
END \$\$;"
sudo -u postgres psql -qc "ALTER ROLE \"$DB_USER\" LOGIN PASSWORD '$DB_PASSWORD';"

sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 \
  || sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"

echo "    bazasi: $DB_NAME (foydalanuvchi: $DB_USER)"

# --------------------------- 6. .env ----------------------------------------
say "6/11 .env yaratilmoqda"
if [[ -f "$APP_DIR/.env" ]]; then
  echo "    .env mavjud — o'zgartirilmaydi"
else
  SECRET_KEY="$(python3 -c 'from django.core.management.utils import get_random_secret_key as g;print(g())' 2>/dev/null || openssl rand -base64 50 | tr -d '\n')"
  BOT_PASSWORD="$(openssl rand -base64 18 | tr -d '/+=' | head -c 18)"

  cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

# TELEGRAM_BOT_TOKEN ni botFather'dan olingan token bilan almashtiring
TELEGRAM_BOT_TOKEN=0000000000:AA...
BOT_API_BASE_URL=http://127.0.0.1:8000/api
BOT_SERVICE_USERNAME=$SERVICE_USER
BOT_SERVICE_PASSWORD=$BOT_PASSWORD
BOT_ADMIN_CHAT_IDS=

MUDDAT_KUN=14
KUNLIK_JARIMA=5000
LIMIT_KITOB=3
TAKLIF_SOAT=24
ESLATMA_KUNLAR_OLDIN=2
JARIMA_ESLATMA_TAKROR_SOAT=24
EOF
  chmod 600 "$APP_DIR/.env"
  chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/.env"
  echo "    BOT_SERVICE_PASSWORD = $BOT_PASSWORD"
fi

# --------------------------- 7. MIGRATE + STATIC ---------------------------
say "7/11 Migratsiya va statik fayllar"
cd "$APP_DIR"
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/python" manage.py migrate --noinput
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/python" manage.py collectstatic --noinput
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/python" manage.py check --deploy 2>&1 | tail -n 20 || true

# superuser (faqat bir marta)
if [[ -z "${ADMIN_USERNAME:-}" ]]; then
  echo
  read -rp "    Django admin login (masalan admin): " ADMIN_USERNAME || ADMIN_USERNAME="admin"
fi
read -rsp "    Parol: " ADMIN_PASSWORD; echo
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/python" manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(username='$ADMIN_USERNAME', defaults={'rol':'administrator','is_staff':True,'is_superuser':True})
u.set_password('$ADMIN_PASSWORD'); u.rol='administrator'; u.is_staff=True; u.is_superuser=True; u.save()
print('admin yaratildi' if created else 'admin yangilandi')" 2>/dev/null \
  || echo "    (admin yaratilmadi — keyin qo'lda qilasiz)"

# --------------------------- 8. SYSTEMD -------------------------------------
say "8/11 systemd xizmatlari (gunicorn, celery, bot)"
cat > /etc/systemd/system/kutubxona.service <<EOF
[Unit]
Description=Kutubxona Django (gunicorn)
After=network.target postgresql.service

[Service]
Type=notify
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn config.wsgi:application \\
  --bind 127.0.0.1:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/kutubxona-celery.service <<EOF
[Unit]
Description=Kutubxona Celery worker
After=network.target postgresql.service redis.service

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/celery -A config worker -l info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/kutubxona-beat.service <<EOF
[Unit]
Description=Kutubxona Celery beat
After=network.target postgresql.service redis.service

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now kutubxona.service
systemctl enable --now kutubxona-celery.service
systemctl enable --now kutubxona-beat.service

# --------------------------- 9. NGINX + SSL ---------------------------------
say "9/11 nginx va SSL"
cat > /etc/nginx/sites-available/kutubxona <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    client_max_body_size 12M;

    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location /media/ {
        alias $APP_DIR/media/;
        expires 30d;
    }
    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

ln -sf /etc/nginx/sites-available/kutubxona /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

ufw allow OpenSSH
ufw allow "Nginx Full"
ufw --force enable
systemctl enable --now fail2ban

# --------------------------- 10. YAKUN --------------------------------------
say "10/11 TLS sertifikat"
if command -v certbot >/dev/null 2>&1 || apt-get install -y -qq certbot python3-certbot-nginx >/dev/null 2>&1; then
  if certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --redirect --non-interactive --agree-tos \
       --register-unsafely-without-email --keep-until-expiring 2>&1 | tail -n 15; then
    echo "    HTTPS tayyor: https://$DOMAIN"
  else
    warn "certbot muvaffaqiyatsiz. DNS serverga yo'naltirilganini tekshiring, keyin:"
    warn "  certbot --nginx -d $DOMAIN -d www.$DOMAIN --redirect"
  fi
else
  warn "certbot o'rnatilmadi. SSL keyin: apt install certbot python3-certbot-nginx"
fi

say "Tayyor!"
cat <<EOF

  Sayt:        https://$DOMAIN
  Katalog:     $APP_DIR
  .env:        $APP_DIR/.env
  Holat:       systemctl status kutubxona kutubxona-celery kutubxona-beat
  Loglar:      journalctl -u kutubxona -f

  BOT token:   $APP_DIR/.env ichidagi TELEGRAM_BOT_TOKEN ni
               haqiqiy token bilan almashtiring, keyin:
               systemctl restart kutubxona

  Admin panel: https://$DOMAIN/admin/

EOF