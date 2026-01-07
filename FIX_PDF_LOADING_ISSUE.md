# Исправление проблемы загрузки PDF книг

## Проблема

Ошибка: **"Nu am putut încărca cartea. Vă rugăm încercați mai târziu."**

**Симптомы:**
- ✅ Сначала работает
- ❌ Через некоторое время перестает работать
- ❌ PDF файлы не загружаются

## Причины проблемы

1. **Отсутствие Range requests поддержки** - PDF.js требует частичной загрузки больших файлов
2. **Таймауты Nginx** - большие PDF файлы не успевают загрузиться
3. **Проблемы с правами доступа** - Gunicorn не может прочитать файлы после перезапуска
4. **Прямой доступ к media файлам** - нет проверки прав доступа

## Решение

### ✅ Что было сделано

#### 1. Создан защищенный view для отдачи PDF

**Файл:** `books/views.py`

Новая функция `serve_book_pdf()`:
- ✅ Проверяет права доступа пользователя
- ✅ Поддерживает Range requests (частичная загрузка)
- ✅ Устанавливает правильные заголовки
- ✅ Кеширование на стороне клиента
- ✅ Обработка ошибок чтения файлов

#### 2. Добавлен URL для безопасной отдачи PDF

**Файл:** `books/urls.py`

```python
path('books/<slug:slug>/pdf/', views.serve_book_pdf, name='serve_book_pdf')
```

#### 3. Обновлен шаблон

**Файл:** `templates/books/book_detail.html`

Изменено:
- ❌ Было: `const pdfUrl = "{{ book.file.url }}";`
- ✅ Стало: `const pdfUrl = "{% url 'serve_book_pdf' book.slug %}";`

---

## Настройка сервера

### Шаг 1: Исправить права доступа к media файлам

```bash
# На сервере:
cd /home/nikita/Desktop/penita

# Исправить права на media папку
sudo chown -R nikita:www-data media/
sudo chmod -R 755 media/

# Убедиться что все PDF читаемые
sudo chmod 644 media/books/*.pdf

# Если используется другой пользователь для gunicorn, замените www-data
```

### Шаг 2: Обновить настройки Gunicorn

Добавьте таймауты в конфигурацию Gunicorn:

**Файл:** `/etc/systemd/system/gunicorn.service` или где у вас конфиг

```ini
[Service]
Environment="TIMEOUT=120"
```

Или в `gunicorn_config.py`:

```python
timeout = 120  # 2 минуты для больших файлов
worker_class = 'sync'
workers = 3
```

### Шаг 3: Настроить Nginx (ВАЖНО!)

**Файл:** `/etc/nginx/sites-available/penitadreptului.md`

Добавьте эти настройки в server block:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name penitadreptului.md;

    # ... другие настройки ...

    # Увеличенные таймауты для больших файлов
    client_max_body_size 10M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    # Проксирование запросов к Django
    location / {
        proxy_pass http://127.0.0.1:8000;  # Порт gunicorn
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Важно для больших файлов
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Статические файлы отдаются напрямую через Nginx
    location /static/ {
        alias /home/nikita/Desktop/penita/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ВАЖНО: НЕ отдавайте media файлы напрямую!
    # Теперь PDF проходят через Django для проверки прав доступа
    # location /media/ {
    #     alias /home/nikita/Desktop/penita/media/;
    # }
}
```

**Проверка и перезагрузка:**

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Шаг 4: Перезапустить Django приложение

```bash
sudo systemctl restart gunicorn
# или
sudo supervisorctl restart penita
```

---

## Проверка исправления

### 1. Проверить права доступа к файлам

```bash
ls -la /home/nikita/Desktop/penita/media/books/

# Все файлы должны быть читаемые:
# -rw-r--r-- nikita www-data file.pdf
```

### 2. Проверить что URL работает

```bash
# Войдите на сайт и скопируйте URL книги, затем:
curl -I "https://penitadreptului.md/books/название-книги/pdf/"

# Должен вернуть:
# HTTP/2 200
# Content-Type: application/pdf
# Content-Length: 1234567
# Accept-Ranges: bytes
```

### 3. Проверить логи

```bash
# Django logs
sudo tail -f /var/log/gunicorn/error.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Искать ошибки связанные с:
# - Permission denied
# - Timeout
# - Cannot open file
```

---

## Дополнительная оптимизация

### Добавить sendfile в Gunicorn (опционально)

В `gunicorn_config.py`:

```python
# Более эффективная отдача файлов
sendfile = True
```

### Мониторинг памяти

```bash
# Проверить что Gunicorn workers не используют слишком много памяти
ps aux | grep gunicorn

# Если workers используют >500MB каждый, уменьшите их количество
```

---

## Частые ошибки и решения

### Ошибка: "Permission denied"

```bash
# Исправить владельца
sudo chown -R nikita:www-data /home/nikita/Desktop/penita/media/

# Исправить права
sudo chmod -R 755 /home/nikita/Desktop/penita/media/
```

### Ошибка: "File not found"

```python
# В Django shell проверьте пути к файлам:
python3 manage.py shell

>>> from books.models import Book
>>> book = Book.objects.first()
>>> print(book.file.path)
>>> import os
>>> os.path.exists(book.file.path)
```

### Ошибка: "Timeout"

```bash
# Увеличить таймауты в nginx.conf:
proxy_read_timeout 300;

# И в gunicorn_config.py:
timeout = 120
```

### Браузер кеширует старую версию

```javascript
// Очистить кеш браузера
// Или добавить version query param
const pdfUrl = "{% url 'serve_book_pdf' book.slug %}?v=" + Date.now();
```

---

## Преимущества нового подхода

✅ **Безопасность** - проверка прав доступа перед отдачей файла
✅ **Надежность** - правильная обработка Range requests для PDF.js
✅ **Производительность** - кеширование на стороне клиента
✅ **Мониторинг** - логирование всех обращений к файлам
✅ **Гибкость** - можно добавить аналитику просмотров

---

## Следующие шаги после деплоя

1. ✅ Перезапустить Gunicorn
2. ✅ Перезагрузить Nginx
3. ✅ Проверить права доступа к media файлам
4. ✅ Тестировать загрузку книг
5. ✅ Мониторить логи первые 24 часа

---

**Дата:** 2026-01-07
**Статус:** ✅ Готово к деплою
