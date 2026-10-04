import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from user.models import User
from dotenv import load_dotenv
load_dotenv()

username = os.environ.get('BOT_SERVICE_USERNAME')
password = os.environ.get('BOT_SERVICE_PASSWORD')

if not username or not password:
    print("ERROR: BOT_SERVICE_USERNAME or BOT_SERVICE_PASSWORD not in .env")
    exit(1)

# Delete any existing bot_service user
User.objects.filter(username=username).delete()

# Create the service account
user = User.objects.create_user(
    username=username,
    password=password,
    full_name="Bot Service Account",
    rol="kutubxonachi",
    telefon="+998000000000",
    is_active=True,
)
print(f"Created service account: {user.username} (rol={user.rol}, active={user.is_active})")

# Verify it works
from rest_framework_simplejwt.tokens import RefreshToken
refresh = RefreshToken.for_user(user)
print(f"Access token: {refresh.access_token}")
print("SUCCESS: Service account ready for bot JWT authentication")