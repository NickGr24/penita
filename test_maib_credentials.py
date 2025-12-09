"""
Test script to verify MAIB credentials
Run this to check if your MAIB Project ID and Secret are correct
"""
import os
import django
import requests
from decouple import config

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penita.settings')
django.setup()

def test_maib_credentials():
    """Test MAIB credentials by trying to generate an access token"""

    # Get credentials from environment
    project_id = config('MAIB_PROJECT_ID', default='')
    project_secret = config('MAIB_PROJECT_SECRET', default='')

    print("=" * 60)
    print("MAIB Credentials Test")
    print("=" * 60)
    print(f"Project ID: {project_id[:15]}..." if len(project_id) > 15 else f"Project ID: {project_id}")
    print(f"Project Secret: {'*' * 20}" if project_secret else "Project Secret: (empty)")
    print()

    # Check if credentials are placeholder values
    if project_id == 'test_project_id' or project_secret == 'test_project_secret':
        print("⚠️  WARNING: You are using placeholder credentials!")
        print("   These will NOT work with the real MAIB API.")
        print("   Please replace them with real credentials from MAIB.")
        print()
        return False

    if not project_id or not project_secret:
        print("❌ ERROR: Credentials are missing!")
        print("   Please add MAIB_PROJECT_ID and MAIB_PROJECT_SECRET to your .env file")
        return False

    # Test API connection
    url = "https://api.maibmerchants.md/v1/generate-token"

    print(f"Testing connection to: {url}")
    print()

    try:
        response = requests.post(
            url,
            json={
                "projectId": project_id,
                "projectSecret": project_secret
            },
            timeout=30
        )

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()

        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {data}")
            print()

            if data.get('ok'):
                print("✅ SUCCESS! Access token generated successfully!")
                print(f"   Token: {data.get('result', {}).get('accessToken', '')[:20]}...")
                return True
            else:
                print("❌ FAILED: MAIB API returned an error")
                errors = data.get('errors', [])
                if errors:
                    for error in errors:
                        print(f"   Error Code: {error.get('errorCode')}")
                        print(f"   Error Message: {error.get('errorMessage')}")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response Body: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        print("   The MAIB API is not responding. Check your internet connection.")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to MAIB API")
        print("   Check your internet connection and firewall settings.")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_maib_credentials()
    print()
    print("=" * 60)

    if success:
        print("Next steps:")
        print("1. Your credentials are working!")
        print("2. You can now test payments on your website")
    else:
        print("Next steps:")
        print("1. Contact MAIB support to get valid credentials")
        print("2. For testing, request SANDBOX/TEST credentials")
        print("3. Update your .env file with the real credentials:")
        print("   MAIB_PROJECT_ID=your_real_project_id")
        print("   MAIB_PROJECT_SECRET=your_real_project_secret")
        print("   MAIB_SIGNATURE_KEY=your_real_signature_key")

    print("=" * 60)
