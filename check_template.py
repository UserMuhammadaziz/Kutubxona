import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.template.loader import get_template
t = get_template('web/index.html')
print("Template path:", t.origin.name)
print("Template content:")
print(t.template.source[:300] if hasattr(t, 'template') and hasattr(t.template, 'source') else 'N/A')
# Also check the actual file
with open(t.origin.name, 'r') as f:
    content = f.read()
    print("\nActual file content:")
    print(content[:300])