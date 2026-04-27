from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_http_methods
import os
from .models import Book
from articles.models import Article

def books_list(request):
    """Публичный список книг для SEO-индексации."""
    books = Book.objects.all().order_by("-id")
    return render(request, 'books/books_list.html', {'books': books})


def book_detail(request, slug):
    """Публичная страница книги для SEO-индексации. PDF защищён отдельно."""
    book = get_object_or_404(Book, slug=slug)

    # Для анонимных пользователей - показываем страницу без доступа к PDF
    if request.user.is_authenticated:
        user_has_access = book.has_user_purchased(request.user)
    else:
        user_has_access = not book.is_paid  # Бесплатные книги доступны всем авторизованным

    # Show purchase button if book is paid and user doesn't have access
    show_purchase_button = book.is_paid and not user_has_access

    # Другие книги того же автора для внутренней перелинковки (SEO)
    other_books = Book.objects.filter(
        author=book.author
    ).exclude(id=book.id)[:4]

    # Связанные статьи автора — кросс-перелинковка book→article
    # и расширение HTML-контента страницы (борьба с thin content)
    primary_author = book.author.split(',')[0].strip()
    related_articles = Article.objects.filter(
        author__icontains=primary_author
    ).order_by('-publication_date')[:4]

    context = {
        'book': book,
        'user_has_access': user_has_access,
        'show_purchase_button': show_purchase_button,
        'other_books': other_books,
        'related_articles': related_articles,
        'primary_author': primary_author,
    }

    return render(request, 'books/book_detail.html', context)


@require_http_methods(["GET"])
def serve_book_pdf(request, slug):
    """
    Безопасная отдача PDF файлов книг.
    Проверяет права доступа пользователя перед отдачей файла.
    Бесплатные книги доступны всем, платные — только авторизованным покупателям.
    """
    book = get_object_or_404(Book, slug=slug)

    # Проверка прав доступа
    if not book.has_user_purchased(request.user):
        if not request.user.is_authenticated:
            return redirect('account_login')
        raise Http404("У вас нет доступа к этой книге")

    # Проверка существования файла
    if not book.file:
        raise Http404("Файл книги не найден")

    file_path = book.file.path

    if not os.path.exists(file_path):
        raise Http404("Файл книги не найден на сервере")

    try:
        # Открываем файл в бинарном режиме
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )

        # Отображение в браузере без возможности скачивания
        response['Content-Disposition'] = 'inline'
        response['Content-Length'] = os.path.getsize(file_path)

        # Запрет кеширования для защиты контента
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'

        return response

    except IOError:
        raise Http404("Ошибка при чтении файла книги")
