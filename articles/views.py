from django.shortcuts import get_object_or_404, render
from .models import Article
from django.db.models import Q

def articles(request):
    query = request.GET.get('q')
    category = request.GET.get('category')  # Получение выбранной категории из параметров запроса
    
    articles = Article.objects.all()

    # Фильтрация по поисковому запросу
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
    print(article.file.url)  # Проверяем правильность URL
    return render(request, 'articles/article_detail.html', {'article': article})
    
