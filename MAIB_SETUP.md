# Настройка MAIB Payment Integration

## Проблема
Когда вы нажимаете "Continuă către plată", вас перебрасывает обратно на страницу книги вместо редиректа на страницу оплаты MAIB.

## Причина
В файле `.env` используются **тестовые заглушки** вместо реальных credentials от MAIB:
```env
MAIB_PROJECT_ID=test_project_id          # ❌ Неправильно
MAIB_PROJECT_SECRET=test_project_secret  # ❌ Неправильно
MAIB_SIGNATURE_KEY=test_signature_key    # ❌ Неправильно
```

Когда код пытается создать платеж, MAIB API отклоняет запрос на генерацию access token из-за неправильных credentials, и пользователь возвращается на страницу книги.

---

## Решение

### Шаг 1: Получите реальные credentials от MAIB

1. **Свяжитесь с MAIB Bank**
   - Email: [ecommerce@maib.md](mailto:ecommerce@maib.md)
   - Телефон: +373 22 268 555

2. **Запросите TEST/SANDBOX credentials** для разработки:
   - `Project ID` (Идентификатор проекта)
   - `Project Secret` (Секретный ключ проекта)
   - `Signature Key` (Ключ для проверки подписи callback)

3. **После тестирования** запросите PRODUCTION credentials для реальных платежей

### Шаг 2: Обновите файл `.env`

```env
# MAIB Payment Settings
MAIB_PROJECT_ID=ваш_реальный_project_id_от_MAIB
MAIB_PROJECT_SECRET=ваш_реальный_project_secret_от_MAIB
MAIB_SIGNATURE_KEY=ваш_реальный_signature_key_от_MAIB
MAIB_TEST_MODE=True  # Используйте True для тестирования
```

### Шаг 3: Протестируйте credentials

Запустите тестовый скрипт:
```bash
python test_maib_credentials.py
```

**Ожидаемый результат:**
```
✅ SUCCESS! Access token generated successfully!
```

**Если видите ошибки:**
- Проверьте, что credentials правильно скопированы
- Убедитесь, что нет лишних пробелов
- Свяжитесь с MAIB для проверки статуса аккаунта

### Шаг 4: Создайте настройки в Django Admin

1. Перейдите в админ-панель: `http://localhost:8000/admin/`
2. Откройте **Payments → MAIB Settings**
3. Создайте новую запись:
   - **Mode**: Test/Sandbox
   - **Project ID**: Ваш Project ID от MAIB
   - **Project Secret**: Ваш Project Secret от MAIB
   - **Signature Key**: Ваш Signature Key от MAIB
   - **API Base URL**: `https://api.maibmerchants.md/v1`
   - **Is Active**: ✅ (отметьте галочку)

### Шаг 5: Протестируйте платеж

1. Перейдите на страницу любой платной книги
2. Нажмите "Cumpără acum"
3. Нажмите "Continuă către plată"
4. **Теперь должно произойти:**
   - Создание платежа в БД
   - Генерация access token от MAIB
   - Получение `payUrl` от MAIB
   - Редирект на страницу оплаты MAIB

---

## Проверка логов

Для отладки проверьте логи Django:

```bash
# Если используете runserver
tail -f /var/log/django/debug.log

# Или смотрите в консоль где запущен runserver
```

**Что искать в логах:**
```
INFO - Attempting to generate token with Project ID: abc123...
INFO - Token generation response status: 200
INFO - Access token generated successfully!
INFO - Redirecting to MAIB payment page: https://...
```

**Если есть ошибки:**
```
ERROR - MAIB API returned error: [{'errorCode': 'INVALID_CREDENTIALS', ...}]
ERROR - Payment initiation failed: Failed to obtain access token
```

---

## Сравнение с документацией MAIB

Ваша реализация **правильная** и соответствует документации:

### ✅ Что реализовано правильно:

1. **Генерация Access Token**
   - Endpoint: `POST https://api.maibmerchants.md/v1/generate-token`
   - Параметры: `projectId`, `projectSecret`

2. **Инициация платежа**
   - Endpoint: `POST https://api.maibmerchants.md/v1/pay`
   - Все обязательные параметры присутствуют:
     - `amount`, `currency`, `clientIp`, `language`
     - `callbackUrl`, `okUrl`, `failUrl`
     - `items` с деталями продукта

3. **Процесс редиректа**
   - После успешного ответа используется `payUrl` для редиректа пользователя

4. **Обработка callback**
   - Endpoint: `POST /payments/callback/`
   - Проверка подписи (signature verification)
   - Обновление статуса платежа

### ⚠️ Что нужно уточнить у MAIB:

1. **Точный формат signature для callback**
   ```python
   # Сейчас используется упрощенная версия:
   signature_string = json.dumps(data, sort_keys=True)

   # MAIB может требовать специфический формат, например:
   # signature_string = f"{payId}|{status}|{amount}|{currency}"
   ```

2. **Формат 3D-Secure данных**
   - Какие поля приходят в callback
   - Как их правильно обрабатывать

---

## Дополнительные настройки

### Настройка Callback URL в production

Убедитесь, что ваш callback URL доступен из интернета:

**Для production:**
```python
callback_url = "https://penitadreptului.md/payments/callback/"
```

**Для локального тестирования** используйте ngrok:
```bash
ngrok http 8000
# Используйте URL вида: https://abc123.ngrok.io/payments/callback/
```

### Тестовые карты MAIB

MAIB предоставляет тестовые карты для sandbox. Запросите их у техподдержки.

Обычно это карты вида:
- **Успешный платеж**: 4111 1111 1111 1111
- **Отклоненный платеж**: 4000 0000 0000 0002
- CVV: любой 3-значный
- Срок: любая будущая дата

---

## Контакты MAIB

- **Email**: ecommerce@maib.md
- **Телефон**: +373 22 268 555
- **Документация**: https://docs.maibmerchants.md/e-commerce/ro
- **Техподдержка**: Через личный кабинет MAIB eCommerce

---

## Checklist для запуска

- [ ] Получены реальные credentials от MAIB (test/sandbox)
- [ ] Обновлен файл `.env` с реальными credentials
- [ ] Запущен `test_maib_credentials.py` - тест прошел успешно
- [ ] Созданы настройки в Django Admin
- [ ] Протестирован платеж - редирект на MAIB работает
- [ ] Настроен callback URL (доступен из интернета)
- [ ] Протестирован полный цикл: инициация → оплата → callback → успех
- [ ] Готовы production credentials для запуска в production
