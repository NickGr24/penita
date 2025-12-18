# 🔧 NGINX Callback 301/405 Error - SOLUTION

## 🎯 Root Cause Identified

From your nginx logs:
```
91.250.245.142 - - [18/Dec/2025:13:07:12] "POST /payment/callback/ HTTP/1.1" 301 178
91.250.245.142 - - [18/Dec/2025:13:07:12] "GET /payment/callback/ HTTP/1.1" 405 0
```

**What's happening:**
1. MAIB sends POST to `/payment/callback/`
2. Nginx returns **301 Moved Permanently**
3. MAIB follows redirect but changes POST → GET (standard HTTP behavior)
4. Django returns **405 Method Not Allowed** (view only accepts POST)

---

## 🔍 ROOT CAUSE CONFIRMED ✅

**MAIB is sending callbacks WITHOUT trailing slash:**

```bash
# ❌ FAILS - MAIB sends this:
POST /payment/callback

# Returns 301 redirect to add trailing slash
# POST becomes GET after redirect → 405 error

# ✅ WORKS - Your Django expects this:
POST /payment/callback/
```

**Test results:**
```bash
curl -X POST http://penitadreptului.md/payment/callback
→ 301 Moved Permanently (redirects to add /)

curl -X POST http://penitadreptului.md/payment/callback/
→ 400/500 (works, no redirect)
```

## 🎯 THE FIX

You have **3 options** to solve this:

---

## ✅ SOLUTION 1: Add URL Without Trailing Slash (QUICKEST)

**This is the fastest fix - takes 30 seconds!**

Edit `payments/urls.py` to accept both URLs (with and without slash):

```python
from django.urls import path
from . import views

urlpatterns = [
    path('payment/initiate/<int:book_id>/', views.initiate_payment, name='initiate_payment'),

    # Accept BOTH versions of callback URL
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/callback', views.payment_callback, name='payment_callback_no_slash'),  # ADD THIS

    path('payment/success/<uuid:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/fail/<uuid:payment_id>/', views.payment_fail, name='payment_fail'),
    path('payment/history/', views.payment_history, name='payment_history'),
    path('payment/status/<uuid:payment_id>/', views.check_payment_status, name='check_payment_status'),
]
```

**Then restart your server:**
```bash
# Development
Ctrl+C, then: python manage.py runserver

# Production
sudo systemctl restart gunicorn
```

**Test it works:**
```bash
curl -X POST http://penitadreptului.md/payment/callback \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'

# Should return 400 error (good - no redirect!)
```

✅ **This fix works immediately and doesn't require nginx changes!**

---

## ✅ SOLUTION 2: Fix Nginx Configuration (BETTER LONG-TERM)

You need to access your nginx config and make POST requests NOT redirect.

### Step 1: Find Your Nginx Config

```bash
# Try to find the config file
sudo find /etc/nginx -name "*.conf" -type f | xargs grep -l "penitadreptului"

# Or check common locations
sudo cat /etc/nginx/sites-available/penitadreptului
sudo cat /etc/nginx/conf.d/penitadreptului.conf
```

### Step 2: Add Special Rule for Callback Endpoint

Your nginx config should look like this:

```nginx
server {
    listen 80;
    server_name penitadreptului.md www.penitadreptului.md;

    # IMPORTANT: Except callback endpoint, redirect all HTTP to HTTPS
    location /payment/callback/ {
        # NO REDIRECT - proxy directly to Django
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable redirects
        proxy_redirect off;
    }

    # Redirect everything else to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name penitadreptului.md www.penitadreptului.md;

    # SSL certificates
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Callback endpoint on HTTPS too
    location /payment/callback/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
    }

    # Other locations
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /static/ {
        alias /home/nikita/Desktop/penita/staticfiles/;
    }

    location /media/ {
        alias /home/nikita/Desktop/penita/media/;
    }
}
```

### Step 3: Test and Reload

```bash
# Test nginx config
sudo nginx -t

# If OK, reload
sudo systemctl reload nginx
```

---

## ✅ SOLUTION 2: Contact MAIB Support

Ask MAIB to check what URL they're actually sending callbacks to:

### Email Template:

```
Subject: Callback URL Verification - Project ID: 9B9C19AE-DC32-4128-9249-16412CCD7E6B

Bună ziua,

I'm receiving 301/405 errors for payment callbacks. My nginx logs show:
- POST /payment/callback/ → 301 redirect
- GET /payment/callback/ → 405 error

Can you please confirm:
1. What exact URL are you sending callbacks to?
   - Is it: http://penitadreptului.md/payment/callback/
   - Or: https://penitadreptului.md/payment/callback/

2. Can you try using HTTPS instead of HTTP?
   - https://penitadreptului.md/payment/callback/

3. Are you following redirects? (POST should not become GET after 301)

My callback endpoint is accessible:
curl -X POST https://penitadreptului.md/payment/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'
→ Returns 200/400 (endpoint works)

Thank you,
[Your name]
```

---

## ✅ SOLUTION 3: Ask MAIB to Use Trailing Slash

Contact MAIB support and ask them to send callbacks to URL **with trailing slash**:

```
❌ Current: http://penitadreptului.md/payment/callback
✅ Correct: http://penitadreptului.md/payment/callback/
                                                      ↑
                                              (add this slash)
```

**However, Solution 1 is faster and works immediately!**

---

## 🧪 TESTING

### Test 1: Check if HTTP redirects

```bash
curl -X POST http://penitadreptului.md/payment/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}' \
  -v
```

**Expected:** Should see either:
- ✅ `200` or `400` response (good - no redirect)
- ❌ `301` or `302` response (bad - needs fix)

### Test 2: Check HTTPS directly

```bash
curl -X POST https://penitadreptului.md/payment/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}' \
  -v
```

**Expected:** ✅ `200` or `400` response (endpoint works)

---

## 📋 CHECKLIST

- [ ] Find nginx config file
- [ ] Add special location block for `/payment/callback/`
- [ ] Ensure callback location does NOT redirect
- [ ] Test with curl (both HTTP and HTTPS)
- [ ] Reload nginx
- [ ] Contact MAIB to confirm they use HTTPS
- [ ] Make new test payment
- [ ] Check logs for callback success

---

## 🎯 QUICK WIN

If you have access to your MAIB merchant panel, check if you can configure the callback URL there. Make sure it's set to:

```
https://penitadreptului.md/payment/callback/
```

(with HTTPS and trailing slash)

---

## 📞 Need Help?

If you can't access nginx config, send me:
1. Output of: `sudo nginx -T` (shows full config)
2. Or the config file location
3. Or SSH access details

I can help create the exact fix for your setup.
