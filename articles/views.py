from django.shortcuts import get_object_or_404, render
from django.http import FileResponse, Http404
from django.views.decorators.http import require_http_methods
from .models import Article
from django.db.models import Q
import os

def articles(request):
    query = request.GET.get('q')
    category = request.GET.get('category')  # Получение выбранной категории из параметров запроса
    articles = Article.objects.all()

    if query:
        articles = articles.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Фильтрация по категории
    if category:
        articles = articles.filter(category=category)
    
    context = {
        'articles': articles,
        'query': query,
        'category': category,
    }
    return render(request, 'articles/articles.html', context)


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    return render(request, 'articles/article_detail.html', {'article': article})


@require_http_methods(["GET"])
def serve_article_pdf(request, slug):
    """
    Публичная отдача PDF файлов статей.
    Статьи доступны всем без авторизации.
    """
    article = get_object_or_404(Article, slug=slug)

    # Проверка существования файла
    if not article.file:
        raise Http404("Файл статьи не найден")

    file_path = article.file.path

    if not os.path.exists(file_path):
        raise Http404("Файл статьи не найден на сервере")

    try:
        # Открываем файл в бинарном режиме
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )

        # Устанавливаем заголовки для корректного отображения в браузере
        response['Content-Disposition'] = f'inline; filename="{article.name}.pdf"'
        response['Content-Length'] = os.path.getsize(file_path)

        # Кеширование на стороне клиента (1 день)
        response['Cache-Control'] = 'public, max-age=86400'

        # Заголовки для поддержки Range requests (важно для больших PDF)
        response['Accept-Ranges'] = 'bytes'

        return response

    except IOError:
        raise Http404("Ошибка при чтении файла статьи")
