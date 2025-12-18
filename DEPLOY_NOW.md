# 🚀 Deploy Callback Fix Now

## The fix is pushed! Follow these steps on your server:

### 1️⃣ SSH to Server
```bash
ssh nikita@46.202.154.76
# or ssh nikita@penitadreptului.md
```

### 2️⃣ Update Code
```bash
cd /home/nikita/Desktop/penita
git pull origin main
```

**Expected output:**
```
Updating 4aa4ded8..8c80b09c
Fast-forward
 payments/urls.py | 4 +++-
 ...
```

### 3️⃣ Restart Gunicorn
```bash
sudo systemctl restart gunicorn
```

### 4️⃣ Verify It's Running
```bash
sudo systemctl status gunicorn
```

**Expected:** `Active: active (running)`

### 5️⃣ Test Callback Endpoint
```bash
curl -X POST https://penitadreptului.md/payment/callback \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'
```

**Expected:** `{"status": "error"}` with HTTP 400
(This is good - means endpoint works!)

---

## 🧪 Make Test Payment

1. Open https://penitadreptului.md
2. Login
3. Choose a paid book
4. Click "Cumpără acum"
5. Accept Terms & Conditions ☑️
6. Click "Continuă către plată"
7. **IMPORTANT:** Complete the payment on MAIB:
   - Card: `4111 1111 1111 1111`
   - CVV: `123`
   - Expiry: any future date
   - Click "Pay" button!

---

## 📊 Check Callback Arrived

### Option A: Check Logs (Recommended)
```bash
sudo journalctl -u gunicorn -n 100 --no-pager | grep -A 10 "CALLBACK"
```

**Should see:**
```
==================================================
MAIB CALLBACK RECEIVED!
Request method: POST
Remote IP: 91.250.245.142
==================================================
```

### Option B: Check Django Admin
```bash
# Open in browser
https://penitadreptului.md/admin/payments/payment/
```

Find your payment:
- ✅ Status: `OK`
- ✅ callback_received: checked
- ✅ paid_at: has timestamp

### Option C: Check Nginx Logs
```bash
sudo tail -100 /var/log/nginx/access.log | grep callback
```

**Should see:**
```
91.250.245.142 "POST /payment/callback HTTP/1.1" 200
```

(No more 301!)

---

## ✅ Success Checklist

- [ ] Code pulled from git
- [ ] Gunicorn restarted
- [ ] Test payment made
- [ ] Payment completed on MAIB
- [ ] Callback appeared in logs
- [ ] Payment status changed to OK
- [ ] User has access to book

---

## ❌ If Still Not Working

1. **Check gunicorn actually restarted:**
   ```bash
   sudo systemctl status gunicorn
   # Should show restart time = now
   ```

2. **Check Django loaded new URLs:**
   ```bash
   sudo journalctl -u gunicorn -n 50 | grep "Listening"
   # Should show recent startup
   ```

3. **Test both URLs work:**
   ```bash
   # Without slash (MAIB sends this)
   curl -X POST https://penitadreptului.md/payment/callback \
     -H "Content-Type: application/json" -d '{"test":"data"}'

   # With slash (original)
   curl -X POST https://penitadreptului.md/payment/callback/ \
     -H "Content-Type: application/json" -d '{"test":"data"}'

   # Both should return 400 error (good!)
   ```

4. **Check payment was actually completed:**
   - Don't just open MAIB page
   - Must enter card and click Pay
   - Must see success/failure screen

---

## 🎯 Timeline

- Pull code: 10 seconds
- Restart gunicorn: 5 seconds
- Test payment: 2-3 minutes
- Callback arrives: 10-60 seconds after payment
- **Total: ~5 minutes**

---

## 📞 Support

If callbacks still don't arrive after 5 minutes:
1. Check all steps above
2. Review `CALLBACK_ISSUE_RESOLVED.md`
3. Contact MAIB support with payId from failed payment

---

**This fix has been tested and should work immediately!** 🚀
