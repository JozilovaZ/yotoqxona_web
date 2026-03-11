#!/bin/bash
set -e

echo "=== Yotoqxona Web Server Setup ==="

# Update system
apt-get update -y
apt-get install -y python3 python3-pip python3-venv nginx git

# Create project directory
mkdir -p /var/www/yotoqxona

# Clone or pull the project
if [ -d "/var/www/yotoqxona/.git" ]; then
    echo "Updating existing repo..."
    cd /var/www/yotoqxona
    git pull origin main
else
    echo "Cloning repo..."
    git clone https://github.com/davronovuz/yotoqxona_web.git /var/www/yotoqxona
fi

cd /var/www/yotoqxona

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Set permissions
chown -R www-data:www-data /var/www/yotoqxona

# Setup systemd service
cp deploy/yotoqxona.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable yotoqxona
systemctl restart yotoqxona

# Setup nginx
cp deploy/nginx.conf /etc/nginx/sites-available/yotoqxona
ln -sf /etc/nginx/sites-available/yotoqxona /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo ""
echo "=== Setup complete! ==="
echo "Site: http://bekendchi.uz"
echo ""
echo "Next steps:"
echo "  1. Point bekendchi.uz DNS A record to: $(curl -s ifconfig.me)"
echo "  2. Install SSL: apt-get install certbot python3-certbot-nginx && certbot --nginx -d bekendchi.uz -d www.bekendchi.uz"
