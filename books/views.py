from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_http_methods
import os
from .models import Book

@login_required
def books_list(request):
    books = Book.objects.all()
    return render(request, 'books/books_list.html', {'books': books})

@login_required
def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)

    # Check if user has access to this book
    user_has_access = book.has_user_purchased(request.user)

    # Show purchase button if book is paid and user doesn't have access
    show_purchase_button = book.is_paid and not user_has_access

    context = {
        'book': book,
        'user_has_access': user_has_access,
        'show_purchase_button': show_purchase_button,
    }

    return render(request, 'books/book_detail.html', context)


@login_required
@require_http_methods(["GET"])
def serve_book_pdf(request, slug):
    """
    Безопасная отдача PDF файлов книг.
    Проверяет права доступа пользователя перед отдачей файла.
    """
    book = get_object_or_404(Book, slug=slug)

    # Проверка прав доступа
    if not book.has_user_purchased(request.user):
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

        # Устанавливаем заголовки для корректного отображения в браузере
        response['Content-Disposition'] = f'inline; filename="{book.title}.pdf"'
        response['Content-Length'] = os.path.getsize(file_path)

        # Кеширование на стороне клиента (1 день)
        response['Cache-Control'] = 'private, max-age=86400'

        # Заголовки для поддержки Range requests (важно для больших PDF)
        response['Accept-Ranges'] = 'bytes'

        return response

    except IOError:
        raise Http404("Ошибка при чтении файла книги")
