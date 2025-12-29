from django.contrib import admin
from .models import News, NewsImage


class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 1
    fields = ('image', 'order')


@admin.register(News)
class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    inlines = [NewsImageInline]