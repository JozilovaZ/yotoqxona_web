"""Remote deployment script via SSH"""
import paramiko
import sys
import time

HOST = '89.116.27.54'
USER = 'root'
PASS = 'Davronov97'

def run_cmd(ssh, cmd, timeout=300):
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    exit_code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out[-2000:] if len(out) > 2000 else out)
    if err.strip():
        print(f"STDERR: {err[-1000:]}")
    if exit_code != 0:
        print(f"EXIT CODE: {exit_code}")
    return exit_code, out, err

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

commands = [
    # Install Docker if not present
    "docker --version || (apt-get update && apt-get install -y ca-certificates curl gnupg && install -m 0755 -d /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && chmod a+r /etc/apt/keyrings/docker.gpg && echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null && apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin)",

    # Install git if not present
    "git --version || apt-get install -y git",

    # Clone or pull project
    "mkdir -p /var/www && cd /var/www && (if [ -d yotoqxona ]; then cd yotoqxona && git pull; else git clone https://github.com/JozilovaZ/yotoqxona_web.git yotoqxona; fi)",

    # Create .env if not exists
    '''cd /var/www/yotoqxona && if [ ! -f .env ]; then SECRET=$(openssl rand -base64 50 | tr -d '\\n/+='); cat > .env << ENVEOF
DJANGO_SECRET_KEY=${SECRET}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=bekendchi.uz,www.bekendchi.uz,89.116.27.54
DJANGO_DB_PATH=/app/data/db.sqlite3
DJANGO_CSRF_TRUSTED_ORIGINS=https://bekendchi.uz,https://www.bekendchi.uz
ENVEOF
echo ".env created"; else echo ".env already exists"; fi''',

    # Use no-SSL config first
    "cd /var/www/yotoqxona && cp nginx/default.nossl.conf nginx/default.conf",

    # Build and start containers
    "cd /var/www/yotoqxona && docker compose up -d --build",

    # Run migrations
    "cd /var/www/yotoqxona && docker compose exec -T web python manage.py migrate",

    # Collect static
    "cd /var/www/yotoqxona && docker compose exec -T web python manage.py collectstatic --noinput",
]

for cmd in commands:
    exit_code, out, err = run_cmd(ssh, cmd, timeout=600)
    if exit_code != 0 and "already" not in (out + err).lower():
        print(f"\nWARNING: Command may have failed (exit {exit_code})")

print("\n=== Base deployment done! Now getting SSL certificate... ===\n")

# Get SSL certificate
exit_code, out, err = run_cmd(ssh,
    "cd /var/www/yotoqxona && docker compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d bekendchi.uz -d www.bekendchi.uz --email admin@bekendchi.uz --agree-tos --no-eff-email --non-interactive",
    timeout=120
)

if exit_code == 0:
    # Switch to SSL config
    run_cmd(ssh, "cd /var/www/yotoqxona && cp nginx/default.conf nginx/default.conf.nossl")

    ssl_conf = '''upstream django {
    server web:8000;
}
server {
    listen 80;
    server_name bekendchi.uz www.bekendchi.uz;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://\\$host\\$request_uri; }
}
server {
    listen 443 ssl;
    server_name bekendchi.uz www.bekendchi.uz;
    ssl_certificate /etc/letsencrypt/live/bekendchi.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bekendchi.uz/privkey.pem;
    client_max_body_size 10M;
    location /static/ { alias /app/staticfiles/; }
    location /media/ { alias /app/media/; }
    location / {
        proxy_pass http://django;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
    }
}'''

    run_cmd(ssh, f"cat > /var/www/yotoqxona/nginx/default.conf << 'SSLEOF'\n{ssl_conf}\nSSLEOF")
    run_cmd(ssh, "cd /var/www/yotoqxona && docker compose restart nginx")

    # Setup cron for auto-renewal
    run_cmd(ssh, '(crontab -l 2>/dev/null; echo "0 3 1 * * cd /var/www/yotoqxona && docker compose run --rm certbot renew && docker compose restart nginx") | crontab -')

    print("\n✅ SSL CONFIGURED SUCCESSFULLY!")
else:
    print("\n⚠️  SSL certificate failed. Site is running on HTTP.")
    print("You can manually get SSL later by running on the server:")
    print("  cd /var/www/yotoqxona && docker compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d bekendchi.uz -d www.bekendchi.uz --email admin@bekendchi.uz --agree-tos --no-eff-email")

# Check status
run_cmd(ssh, "cd /var/www/yotoqxona && docker compose ps")

print("\n========================================")
print("  DEPLOYMENT COMPLETE!")
print("  http://bekendchi.uz")
print("========================================")
print("\nSuperuser yaratish uchun serverda:")
print("  cd /var/www/yotoqxona && docker compose exec web python manage.py createsuperuser")

ssh.close()
