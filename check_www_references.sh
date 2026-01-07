#!/bin/bash

# Скрипт для проверки ссылок на www версию сайта

echo "======================================"
echo "Проверка ссылок на www.penitadreptului.md"
echo "======================================"
echo ""

echo "1. Проверка templates..."
www_in_templates=$(grep -r "www.penitadreptului.md" templates/ 2>/dev/null | grep -v ".swp" || echo "")
if [ -z "$www_in_templates" ]; then
    echo "✅ В templates нет ссылок на www версию"
else
    echo "⚠️  Найдены ссылки на www в templates:"
    echo "$www_in_templates"
fi
echo ""

echo "2. Проверка settings.py..."
www_in_settings=$(grep "www.penitadreptului.md" penita/settings.py 2>/dev/null | grep -v "ALLOWED_HOSTS" | grep -v "CSRF_TRUSTED_ORIGINS" || echo "")
if [ -z "$www_in_settings" ]; then
    echo "✅ В settings.py нет проблемных ссылок на www (кроме ALLOWED_HOSTS)"
else
    echo "⚠️  Найдены ссылки на www в settings.py:"
    echo "$www_in_settings"
fi
echo ""

echo "3. Проверка Python файлов..."
www_in_python=$(find . -name "*.py" -type f ! -path "./venv*/*" ! -path "./.env/*" -exec grep -l "www.penitadreptului.md" {} \; 2>/dev/null || echo "")
if [ -z "$www_in_python" ]; then
    echo "✅ В Python файлах нет ссылок на www версию"
else
    echo "⚠️  Найдены файлы со ссылками на www:"
    echo "$www_in_python"
fi
echo ""

echo "4. Проверка статических файлов..."
www_in_static=$(grep -r "www.penitadreptului.md" main/static/ 2>/dev/null || echo "")
if [ -z "$www_in_static" ]; then
    echo "✅ В статических файлах нет ссылок на www версию"
else
    echo "⚠️  Найдены ссылки на www в статических файлах:"
    echo "$www_in_static"
fi
echo ""

echo "5. Проверка базы данных (django_site)..."
site_domain=$(psql -U nikita -d penita -t -c "SELECT domain FROM django_site WHERE id=1;" 2>/dev/null | xargs)
if [ "$site_domain" = "penitadreptului.md" ]; then
    echo "✅ Домен в django_site правильный: $site_domain"
elif [ "$site_domain" = "www.penitadreptului.md" ]; then
    echo "❌ Домен в django_site неправильный: $site_domain"
    echo "   Исправьте командой:"
    echo "   psql -U nikita -d penita -c \"UPDATE django_site SET domain='penitadreptului.md' WHERE id=1;\""
else
    echo "⚠️  Домен в django_site: $site_domain (не является основным доменом)"
fi
echo ""

echo "======================================"
echo "Проверка завершена"
echo "======================================"
