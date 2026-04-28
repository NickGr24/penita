from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse, Http404
from django.views.decorators.http import require_http_methods
from .models import Article
from books.models import Book
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
    try:
        article = Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        # 301-редирект со старого (обрезанного) URL на новый — для сохранения SEO-веса
        legacy = Article.objects.filter(legacy_slug=slug).first()
        if legacy:
            return redirect('article_detail', slug=legacy.slug, permanent=True)
        raise Http404("Articolul nu a fost găsit")

    # Проверяем, что PDF физически существует на диске
    # (поле article.file в БД может ссылаться на удалённый файл)
    pdf_available = bool(article.file) and os.path.exists(article.file.path) if article.file else False

    # Похожие статьи той же категории для внутренней перелинковки (SEO)
    related_articles = Article.objects.filter(
        category=article.category
    ).exclude(id=article.id).order_by('-publication_date')[:4]

    # Книги того же автора — кросс-перелинковка статья→книга (конверсия + SEO)
    recommended_books = Book.objects.filter(
        author__icontains=article.author.split(',')[0].strip()
    ).order_by('-created_at')[:3]

    return render(request, 'articles/article_detail.html', {
        'article': article,
        'pdf_available': pdf_available,
        'related_articles': related_articles,
        'recommended_books': recommended_books,
    })


@require_http_methods(["GET"])
def serve_article_pdf(request, slug):
    """
    Публичная отдача PDF файлов статей.
    Статьи доступны всем без авторизации.
    """
    try:
        article = Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        legacy = Article.objects.filter(legacy_slug=slug).first()
        if legacy:
            return redirect('serve_article_pdf', slug=legacy.slug, permanent=True)
        raise Http404("Fișierul articolului nu a fost găsit")

    # Проверка существования файла
    if not article.file:
        raise Http404("Fișierul articolului nu a fost găsit")

    file_path = article.file.path

    if not os.path.exists(file_path):
        raise Http404("Fișierul articolului nu a fost găsit pe server")

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
        raise Http404("Eroare la citirea fișierului articolului")
