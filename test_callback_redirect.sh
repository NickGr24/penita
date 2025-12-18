#!/bin/bash

# 🔍 MAIB Callback Redirect Diagnostic Script
# This script tests if your callback endpoint is redirecting POST requests

echo "=========================================="
echo "🔍 MAIB Callback Redirect Test"
echo "=========================================="
echo ""

# Test 1: HTTP POST
echo "Test 1: POST to HTTP (port 80)"
echo "URL: http://penitadreptului.md/payment/callback/"
echo "------------------------------------------"
HTTP_RESPONSE=$(curl -X POST http://penitadreptului.md/payment/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}' \
  -w "\nHTTP_CODE:%{http_code}\nREDIRECT_URL:%{redirect_url}\n" \
  -s -L)

echo "$HTTP_RESPONSE"
echo ""

HTTP_CODE=$(echo "$HTTP_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
REDIRECT_URL=$(echo "$HTTP_RESPONSE" | grep "REDIRECT_URL" | cut -d: -f2-)

if [[ "$HTTP_CODE" == "301" ]] || [[ "$HTTP_CODE" == "302" ]] || [[ "$HTTP_CODE" == "307" ]] || [[ "$HTTP_CODE" == "308" ]]; then
    echo "❌ PROBLEM FOUND: HTTP redirects to HTTPS!"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Redirect URL: $REDIRECT_URL"
    echo "   This causes POST to become GET!"
    echo ""
elif [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "400" ]] || [[ "$HTTP_CODE" == "500" ]]; then
    echo "✅ HTTP POST works (no redirect)"
    echo ""
else
    echo "⚠️  Unexpected response: $HTTP_CODE"
    echo ""
fi

# Test 2: HTTPS POST
echo "Test 2: POST to HTTPS (port 443)"
echo "URL: https://penitadreptului.md/payment/callback/"
echo "------------------------------------------"
HTTPS_RESPONSE=$(curl -X POST https://penitadreptului.md/payment/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}' \
  -w "\nHTTP_CODE:%{http_code}\n" \
  -s)

echo "$HTTPS_RESPONSE"
echo ""

HTTPS_CODE=$(echo "$HTTPS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

if [[ "$HTTPS_CODE" == "200" ]] || [[ "$HTTPS_CODE" == "400" ]] || [[ "$HTTPS_CODE" == "500" ]]; then
    echo "✅ HTTPS POST works"
    echo ""
elif [[ "$HTTPS_CODE" == "301" ]] || [[ "$HTTPS_CODE" == "302" ]]; then
    echo "❌ HTTPS also redirects!"
    echo ""
else
    echo "⚠️  Unexpected response: $HTTPS_CODE"
    echo ""
fi

# Test 3: WWW subdomain
echo "Test 3: POST to WWW subdomain"
echo "URL: https://www.penitadreptului.md/payment/callback/"
echo "------------------------------------------"
WWW_RESPONSE=$(curl -X POST https://www.penitadreptului.md/payment/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}' \
  -w "\nHTTP_CODE:%{http_code}\nREDIRECT_URL:%{redirect_url}\n" \
  -s -L)

echo "$WWW_RESPONSE"
echo ""

WWW_CODE=$(echo "$WWW_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

if [[ "$WWW_CODE" == "301" ]] || [[ "$WWW_CODE" == "302" ]]; then
    echo "⚠️  WWW subdomain redirects to non-WWW"
    echo ""
fi

# Summary
echo "=========================================="
echo "📊 DIAGNOSIS SUMMARY"
echo "=========================================="
echo ""

if [[ "$HTTP_CODE" == "301" ]] || [[ "$HTTP_CODE" == "302" ]]; then
    echo "🎯 ROOT CAUSE: HTTP to HTTPS redirect"
    echo ""
    echo "SOLUTION:"
    echo "1. Configure MAIB to use HTTPS callback URL:"
    echo "   https://penitadreptului.md/payment/callback/"
    echo ""
    echo "2. OR: Configure nginx to NOT redirect /payment/callback/"
    echo "   (see NGINX_CALLBACK_FIX.md for details)"
    echo ""
elif [[ "$HTTPS_CODE" == "200" ]] || [[ "$HTTPS_CODE" == "400" ]]; then
    echo "✅ Callback endpoint works correctly on HTTPS!"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Verify MAIB is sending to HTTPS (not HTTP)"
    echo "2. Contact MAIB support to confirm callback URL"
    echo "3. Check MAIB merchant panel settings"
    echo ""
else
    echo "⚠️  Unexpected results - manual investigation needed"
    echo ""
fi

echo "=========================================="
echo "📞 For detailed fix instructions, see:"
echo "   NGINX_CALLBACK_FIX.md"
echo "=========================================="
