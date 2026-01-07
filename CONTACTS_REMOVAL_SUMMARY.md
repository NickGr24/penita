# Удаление страницы "Контакты"

## Выполненные изменения

### ✅ 1. Удален URL маршрут
**Файл:** `main/urls.py`
- Удалена строка: `path('contacts/', views.contacts, name='contacts')`
- Результат: `/contacts/` вернет 404 ошибку

### ✅ 2. Удалена view функция
**Файл:** `main/views.py`
- Удалена функция `def contacts(request)`
- Код очищен от неиспользуемой логики

### ✅ 3. Исключено из Sitemap
**Файл:** `penita/sitemaps.py`
- Удалено `'contacts'` из списка статических страниц
- Результат: страница не будет в sitemap.xml

### ✅ 4. Удален шаблон
**Файл:** `templates/contacts.html`
- Файл полностью удален
- Освобождено место на диске

### ✅ 5. Проверена навигация
**Файл:** `templates/navbar.html`
- Ссылок на контакты не найдено
- Навигация не требует изменений

## Проверка

После перезапуска Django:
- ✅ URL `/contacts/` не будет доступен (404)
- ✅ Sitemap не будет включать контакты
- ✅ Нет битых ссылок в навигации
- ✅ Нет упоминаний в коде

## Следующие шаги

1. **Перезапустите Django приложение:**
   ```bash
   sudo systemctl restart gunicorn
   ```

2. **Проверьте sitemap:**
   ```bash
   curl https://penitadreptului.md/sitemap.xml | grep -i contact
   # Не должно быть результатов
   ```

3. **Обновите Google Search Console:**
   - Дождитесь автоматического обновления sitemap (24-48 часов)
   - Или запросите переиндексацию вручную

## Изменённые файлы

```
modified:   main/urls.py
modified:   main/views.py
modified:   penita/sitemaps.py
deleted:    templates/contacts.html
```

---

**Дата:** 2026-01-07
**Статус:** ✅ Завершено
