"""Create superuser on remote server via SSH"""
import paramiko

HOST = '89.116.27.54'
USER = 'root'
PASS = 'Davronov97'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

script = """
from accounts.models import User
# Delete old Jozilova if exists
User.objects.filter(username='Jozilova').delete()
# Create superuser
u = User.objects.create_superuser(username='Jozilova', password='123')
u.role = 'admin'
u.save()
print('Superuser Jozilova created successfully!')
print('All users:', list(User.objects.values_list('username', flat=True)))
"""

cmd = f'cd /var/www/yotoqxona && docker compose exec -T web python manage.py shell -c "{script}"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print("STDERR:", err[-1000:])

ssh.close()
