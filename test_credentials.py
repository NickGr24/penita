#!/usr/bin/env python3
"""Quick test for MAIB credentials"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penita.settings')
django.setup()

from payments.models import MAIBSettings
from payments.services import MAIBPaymentService

print("=" * 70)
print("MAIB CREDENTIALS TEST")
print("=" * 70)
print()

# Check database settings
print("1. Checking MAIBSettings in database...")
settings = MAIBSettings.objects.filter(is_active=True).first()

if settings:
    print(f"   ✓ Active settings found")
    print(f"   Mode: {settings.mode}")
    print(f"   Project ID: {settings.project_id[:20]}...")
    print(f"   API URL: {settings.api_base_url}")
else:
    print("   ✗ No active MAIBSettings found!")
    print("   Please create settings in Django Admin")
    exit(1)

print()
print("2. Testing access token generation...")

service = MAIBPaymentService(test_mode=(settings.mode == 'test'))
token = service.generate_access_token()

if token:
    print(f"   ✓ Access token generated successfully!")
    print(f"   Token: {token[:30]}...")
else:
    print("   ✗ Failed to generate access token")
    print("   Check your credentials in Django Admin")
    exit(1)

print()
print("=" * 70)
print("✓ ALL CHECKS PASSED!")
print("Your MAIB credentials are working correctly.")
print("=" * 70)
