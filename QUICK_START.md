# Быстрый старт - Исправление SEO проблем

## Что было исправлено

✅ Создан Django middleware для редиректа с www на версию без www
✅ Обновлен домен в Django Sites framework
✅ Проверены все canonical теги
✅ Подготовлена конфигурация Nginx

## Запуск изменений (3 простых шага)

### 1. Перезапустите Django приложение

```bash
# Вариант A: Если используете systemd/gunicorn
sudo systemctl restart gunicorn

# Вариант B: Если используете supervisor
sudo supervisorctl restart penita

# Вариант C: Если используете другой менеджер процессов
# Перезапустите ваш Django процесс
```

### 2. Настройте Nginx (опционально, но рекомендуется)

```bash
# Откройте конфигурацию nginx
sudo nano /etc/nginx/sites-available/penitadreptului.md

# Добавьте редирект (см. nginx-redirect-config.md)
# Затем:
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Протестируйте редирект

```bash
# Проверьте, что редирект работает
curl -I https://www.penitadreptului.md

# Вы должны увидеть:
# HTTP/2 301
# location: https://penitadreptului.md/
```

## Google Search Console

После запуска изменений:

1. Откройте [Google Search Console](https://search.google.com/search-console)
2. Перейдите в раздел "Покрытие" (Coverage)
3. Нажмите "Запросить индексирование" для проблемных URL
4. Подождите 1-2 недели для переиндексации

## Проверка результата

Через несколько дней проверьте:
- [ ] Редирект работает (curl -I https://www.penitadreptului.md)
- [ ] Google начал переиндексацию
- [ ] Количество ошибок в Search Console уменьшается

## Файлы для справки

- `SEO-FIX-INSTRUCTIONS.md` - Полная инструкция с деталями
- `nginx-redirect-config.md` - Готовая конфигурация Nginx
- `check_www_references.sh` - Скрипт проверки ссылок на www
- `penita/middleware/redirect.py` - Django middleware для редиректа

## Помощь

Если что-то не работает:
1. Проверьте логи: `sudo tail -f /var/log/gunicorn/error.log`
2. Проверьте статус: `sudo systemctl status gunicorn`
3. Запустите проверку: `./check_www_references.sh`
