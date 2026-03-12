#!/bin/bash
# Server deployment script for bekendchi.uz
# Run on the server: bash server_setup.sh

set -e

echo "=== 1. Installing Docker ==="
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "=== 2. Cloning project ==="
mkdir -p /var/www
cd /var/www
if [ -d "yotoqxona" ]; then
    cd yotoqxona && git pull
else
    git clone https://github.com/JozilovaZ/yotoqxona_web.git yotoqxona
    cd yotoqxona
fi

echo "=== 3. Creating .env file ==="
if [ ! -f .env ]; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 50)
    cat > .env << ENVEOF
DJANGO_SECRET_KEY=${SECRET}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=bekendchi.uz,www.bekendchi.uz,89.116.27.54
DJANGO_DB_PATH=/app/data/db.sqlite3
DJANGO_CSRF_TRUSTED_ORIGINS=https://bekendchi.uz,https://www.bekendchi.uz
ENVEOF
    echo ".env file created"
fi

echo "=== 4. First run without SSL (to get certbot certificate) ==="
cp nginx/default.nossl.conf nginx/default.conf
docker compose up -d --build

echo "=== 5. Running migrations ==="
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput

echo "=== 6. Getting SSL certificate ==="
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d bekendchi.uz \
    -d www.bekendchi.uz \
    --email admin@bekendchi.uz \
    --agree-tos \
    --no-eff-email

echo "=== 7. Switching to SSL nginx config ==="
cat > nginx/default.conf << 'NGINXEOF'
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name bekendchi.uz www.bekendchi.uz;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name bekendchi.uz www.bekendchi.uz;

    ssl_certificate /etc/letsencrypt/live/bekendchi.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bekendchi.uz/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXEOF

docker compose restart nginx

echo "=== 8. Setting up SSL auto-renewal ==="
(crontab -l 2>/dev/null; echo "0 3 * * * cd /var/www/yotoqxona && docker compose run --rm certbot renew && docker compose restart nginx") | crontab -

echo ""
echo "========================================="
echo "  DEPLOYMENT COMPLETE!"
echo "  Site: https://bekendchi.uz"
echo "========================================="
echo ""
echo "Create superuser:"
echo "  cd /var/www/yotoqxona && docker compose exec web python manage.py createsuperuser"
