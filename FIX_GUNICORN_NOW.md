# 🔧 Fix Gunicorn Socket Issue

## Problem: Gunicorn socket not found

Nginx error shows:
```
connect() to unix:/run/penita/penita.sock failed (2: No such file or directory)
```

This means gunicorn didn't start properly.

---

## 1️⃣ Check Gunicorn Status

```bash
sudo systemctl status gunicorn
```

**If you see:**
- ❌ `Active: failed` or `inactive (dead)` - Gunicorn crashed
- ✅ `Active: active (running)` - Gunicorn is running

---

## 2️⃣ Check What Went Wrong

```bash
# See recent gunicorn logs
sudo journalctl -u gunicorn -n 50 --no-pager

# Look for errors at the end
sudo journalctl -u gunicorn -xe
```

**Common errors:**
- Python module not found
- Permission denied
- Port already in use
- Socket path doesn't exist

---

## 3️⃣ Check Gunicorn Configuration

```bash
# Check gunicorn service file
sudo cat /etc/systemd/system/gunicorn.service

# Or if it's in different location
sudo systemctl cat gunicorn
```

**Look for:**
- `ExecStart=` - Should point to gunicorn binary
- `WorkingDirectory=` - Should be `/root/penita` or `/home/nikita/Desktop/penita`
- Socket path or port binding

---

## 4️⃣ Verify Socket Directory Exists

```bash
# Check if /run/penita/ directory exists
ls -la /run/penita/

# If not, create it
sudo mkdir -p /run/penita
sudo chown www-data:www-data /run/penita
```

---

## 5️⃣ Try Manual Gunicorn Start (Debug)

```bash
# Go to project directory
cd /root/penita  # or wherever your project is

# Try starting gunicorn manually
gunicorn --bind unix:/run/penita/penita.sock penita.wsgi:application

# If error appears, read the error message
# It will tell you exactly what's wrong
```

**Press Ctrl+C to stop after testing**

---

## 6️⃣ Alternative: Use TCP Instead of Socket

If socket keeps failing, edit nginx config to use TCP:

**Edit nginx config:**
```bash
sudo nano /etc/nginx/sites-available/default
# Or wherever your config is
```

**Change from:**
```nginx
proxy_pass http://unix:/run/penita/penita.sock;
```

**To:**
```nginx
proxy_pass http://127.0.0.1:8000;
```

**Then restart nginx:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

**And start gunicorn on port 8000:**
```bash
# In gunicorn.service file, change:
# ExecStart=... --bind unix:/run/penita/penita.sock ...
# To:
# ExecStart=... --bind 127.0.0.1:8000 ...
```

---

## 7️⃣ Restart Everything

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart gunicorn
sudo systemctl restart gunicorn

# Check status
sudo systemctl status gunicorn

# Restart nginx
sudo systemctl reload nginx
```

---

## 🧪 Test It Works

```bash
# Test callback endpoint
curl -X POST https://penitadreptului.md/payment/callback \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'

# Should return: {"status": "error"} with 400 or 500
# NOT 502 Bad Gateway!
```

---

## 📊 Quick Diagnostic Commands

Run all these and send me the output:

```bash
echo "=== Gunicorn Status ==="
sudo systemctl status gunicorn

echo ""
echo "=== Socket File ==="
ls -la /run/penita/ 2>/dev/null || echo "Directory doesn't exist"

echo ""
echo "=== Gunicorn Config ==="
sudo systemctl cat gunicorn

echo ""
echo "=== Recent Errors ==="
sudo journalctl -u gunicorn -n 20 --no-pager

echo ""
echo "=== Test Endpoint ==="
curl -X POST https://penitadreptului.md/payment/callback \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}' \
  -w "\nHTTP_CODE:%{http_code}\n"
```

Send me this output and I'll tell you exactly what to fix!
