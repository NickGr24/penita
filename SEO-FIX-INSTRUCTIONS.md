# Инструкции по исправлению проблем с индексацией Google

## Проблема

Google Search Console показывает ошибки:
- **"Вариант страницы с тегом canonical"** - 3 страницы
- **"Страница является копией. Канонический вариант не выбран пользователем."** - 1 страница

### Причина

Сайт доступен по двум версиям:
- `www.penitadreptului.md` (Google сканирует эту версию)
- `penitadreptului.md` (canonical теги указывают на эту версию)

Это создает конфликт: Google видит страницы как дубликаты.

## Что было сделано

### 1. ✅ Создан Django middleware для редиректа

**Файл:** `penita/middleware/redirect.py`

Middleware автоматически перенаправляет все запросы с `www.penitadreptului.md` на `penitadreptului.md` с HTTP кодом 301 (постоянный редирект).

**Добавлено в:** `penita/settings.py` (строка 50)

### 2. ✅ Обновлен Django Sites framework

**База данных:** Таблица `django_site`

Домен обновлен с `example.com` на `penitadreptului.md`. Теперь sitemap и все автоматически генерируемые URL будут использовать правильный домен.

### 3. ✅ Проверены canonical теги

Все canonical теги в шаблонах уже правильно настроены и указывают на версию без `www`:
- `/templates/base.html` - базовый canonical тег
- Все страницы наследуют правильные canonical URL

### 4. ✅ Подготовлена конфигурация Nginx

**Файл:** `nginx-redirect-config.md`

Содержит готовую конфигурацию для редиректа на уровне веб-сервера (более эффективно, чем Django middleware).

## Следующие шаги

### Шаг 1: Перезапустите Django приложение

После добавления middleware нужно перезапустить приложение:

```bash
# Если используете systemd
sudo systemctl restart gunicorn  # или uwsgi

# Если используете supervisor
sudo supervisorctl restart penita

# Или просто перезапустите процесс Django
```

### Шаг 2: Настройте Nginx (рекомендуется)

Хотя Django middleware уже работает, лучше добавить редирект на уровне Nginx для производительности:

1. Откройте файл конфигурации nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/penitadreptului.md
   ```

2. Добавьте server block для редиректа (см. `nginx-redirect-config.md`)

3. Проверьте конфигурацию:
   ```bash
   sudo nginx -t
   ```

4. Перезагрузите nginx:
   ```bash
   sudo systemctl reload nginx
   ```

### Шаг 3: Проверьте редирект

```bash
# Проверьте, что редирект работает
curl -I https://www.penitadreptului.md

# Ожидаемый результат:
# HTTP/2 301
# location: https://penitadreptului.md/
```

### Шаг 4: Google Search Console

1. **Запросите переиндексацию** главной страницы и проблемных URL через Google Search Console

2. **Отправьте обновленный sitemap:**
   ```
   https://penitadreptului.md/sitemap.xml
   ```

3. **Подождите 1-2 недели** для повторного сканирования Google

4. **Проверьте статус** в разделе "Покрытие" (Coverage)

### Шаг 5: Мониторинг

- Следите за отчетами Google Search Console
- Ошибки "Вариант страницы с тегом canonical" должны исчезнуть после переиндексации
- Google передаст весь SEO-вес на версию без `www`

## Дополнительные рекомендации

### Robots.txt

Убедитесь, что в `robots.txt` используется правильный домен для sitemap:

```
Sitemap: https://penitadreptului.md/sitemap.xml
```

### Проверьте внутренние ссылки

Убедитесь, что все внутренние ссылки на сайте используют относительные пути или домен без `www`:

```bash
# Поиск ссылок с www в шаблонах
grep -r "www.penitadreptului.md" templates/
```

### Analytics и соцсети

Если используете:
- **Google Analytics**: домен уже правильный (не зависит от www)
- **Facebook Pixel**: работает с обеими версиями
- **Open Graph теги**: уже используют правильный домен (см. `base.html`)

## Ожидаемый результат

После выполнения всех шагов:
- ✅ Все запросы на `www.penitadreptului.md` будут автоматически перенаправляться на `penitadreptului.md`
- ✅ Google переиндексирует страницы и признает `penitadreptului.md` как канонический вариант
- ✅ Ошибки в Google Search Console исчезнут
- ✅ SEO-вес будет консолидирован на одном домене

## Поддержка

Если возникнут проблемы:
1. Проверьте логи Django: `/var/log/gunicorn/error.log`
2. Проверьте логи Nginx: `/var/log/nginx/error.log`
3. Используйте инструменты проверки редиректов: https://httpstatus.io/

---

**Важно:** Изменения в Google Search Console могут занять от нескольких дней до нескольких недель. Это нормально.
