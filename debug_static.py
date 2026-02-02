
import os
import sys
import django

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings')
django.setup()

from django.conf import settings

print("\n" + "="*50)
print("DEBUG STATIC FILES CONFIGURATION")
print("="*50)
print(f"BASE_DIR:    {settings.BASE_DIR}")
print(f"STATIC_URL:  {settings.STATIC_URL}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print("="*50)
print("\nINSTRUCTIONS FOR PYTHONANYWHERE 'WEB' TAB:")
print("1. Scroll to 'Static files' section.")
print(f"2. URL:       {settings.STATIC_URL}")
print(f"3. Directory: {settings.STATIC_ROOT}")
print("="*50 + "\n")
