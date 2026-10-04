import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import authenticate
from dotenv import load_dotenv
load_dotenv()

username = os.environ.get('BOT_SERVICE_USERNAME')
password = os.environ.get('BOT_SERVICE_PASSWORD')

print(f"Testing auth for: {username}")

user = authenticate(username=username, password=password)
print(f"authenticate() returned: {user}")
if user:
    print(f"  username={user.username}, rol={user.rol}, active={user.is_active}")
    print(f"  check_password={user.check_password(password)}")
else:
    print("authenticate() returned None")

from user.models import User
try:
    u = User.objects.get(username=username)
    print(f"\nUser from DB: {u.username}, password_valid={u.check_password(password)}")
except User.DoesNotExist:
    print("User does not exist!")