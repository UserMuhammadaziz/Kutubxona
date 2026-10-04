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
if user:
    print(f"SUCCESS: User authenticated - {user.username}, rol={user.rol}, active={user.is_active}")
else:
    print("FAILED: authenticate() returned None")

# Also check the user exists
from user.models import User
try:
    u = User.objects.get(username=username)
    print(f"User exists: {u.username}, password valid: {u.check_password(password)}")
except User.DoesNotExist:
    print("User does not exist!")