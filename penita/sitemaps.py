from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from main.models import News
from articles.models import Article
from books.models import Book


class StaticViewSitemap(Sitemap):
    """Sitemap для статических страниц"""
    protocol = 'https'
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return [
            'home',
            'articles',
            'books_list',
            'osoianu',
            'ostavciuc',
            'terms_and_conditions',
            'privacy_policy',
        ]

    def location(self, item):
        return reverse(item)


class ArticleSitemap(Sitemap):
    """Sitemap для статей"""
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Article.objects.all()

    def location(self, obj):
        return reverse('article_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.publication_date


class BookSitemap(Sitemap):
    """Sitemap для книг"""
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        return Book.objects.all()

    def location(self, obj):
        return reverse('book_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        """Дата последнего обновления для Google"""
        return obj.updated_at or obj.created_at


class NewsSitemap(Sitemap):
    """Sitemap для новостей"""
    protocol = 'https'
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return News.objects.all()

    def location(self, obj):
        return reverse('news_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at or obj.created_at


sitemaps = {
    'static': StaticViewSitemap,
    'articles': ArticleSitemap,
    'books': BookSitemap,
    'news': NewsSitemap,
}
