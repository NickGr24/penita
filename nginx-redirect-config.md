# Конфигурация Nginx для редиректа с www на версию без www

## Вариант 1: Отдельный server block для редиректа (Рекомендуется)

Добавьте этот блок в вашу конфигурацию nginx (обычно в `/etc/nginx/sites-available/penitadreptului.md`):

```nginx
# Редирект с www на версию без www
server {
    listen 80;
    listen 443 ssl http2;
    server_name www.penitadreptului.md;

    # SSL сертификаты (если используете HTTPS)
    ssl_certificate /etc/letsencrypt/live/penitadreptului.md/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/penitadreptului.md/privkey.pem;

    # 301 редирект на версию без www
    return 301 $scheme://penitadreptului.md$request_uri;
}

# Основной server block для версии без www
server {
    listen 80;
    listen 443 ssl http2;
    server_name penitadreptului.md;

    # Ваша текущая конфигурация...
}
```

## Вариант 2: Условный редирект внутри основного server block

Если вы хотите использовать один server block:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name penitadreptului.md www.penitadreptului.md;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/penitadreptului.md/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/penitadreptului.md/privkey.pem;

    # Редирект с www на версию без www
    if ($host = 'www.penitadreptului.md') {
        return 301 $scheme://penitadreptului.md$request_uri;
    }

    # Ваша текущая конфигурация...
}
```

## Проверка и применение изменений

1. Проверьте конфигурацию nginx на наличие синтаксических ошибок:
   ```bash
   sudo nginx -t
   ```

2. Если проверка прошла успешно, перезагрузите nginx:
   ```bash
   sudo systemctl reload nginx
   # или
   sudo service nginx reload
   ```

## Обновление SSL сертификата

Если вы используете Let's Encrypt, убедитесь, что сертификат включает обе версии домена:

```bash
sudo certbot certonly --nginx -d penitadreptului.md -d www.penitadreptului.md
```

## Проверка редиректа

После настройки проверьте редирект:

```bash
curl -I https://www.penitadreptului.md
```

Вы должны увидеть:
```
HTTP/2 301
location: https://penitadreptului.md/
```

## Примечания

- **Django middleware** уже настроен и работает как fallback
- **Nginx редирект** более эффективен (обрабатывается на уровне веб-сервера)
- Используйте оба подхода для максимальной надежности
- 301 редирект - постоянный, Google передаст весь SEO-вес на основной домен
