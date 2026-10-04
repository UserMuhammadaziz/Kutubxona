import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from user.models import User
from django.conf import settings

print("Service username from settings:", getattr(settings, 'BOT_SERVICE_USERNAME', 'NOT SET'))
print("Service password from settings:", getattr(settings, 'BOT_SERVICE_PASSWORD', 'NOT SET'))

# Check .env
print("\n--- .env check ---")
from dotenv import load_dotenv
load_dotenv()
print("BOT_SERVICE_USERNAME:", os.environ.get('BOT_SERVICE_USERNAME'))
print("BOT_SERVICE_PASSWORD:", os.environ.get('BOT_SERVICE_PASSWORD'))

# Check DB
print("\n--- DB users with rol=kutubxonachi ---")
for u in User.objects.filter(rol='kutubxonachi'):
    print(f"  {u.username} | {u.full_name} | active={u.is_active}")