from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'author', 'category', 'publication_date', 'has_seo_content')
    list_filter = ('category', 'author')
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'file', 'author', 'category')
        }),
        ('SEO Content', {
            'classes': ('collapse',),
            'fields': ('excerpt', 'seo_content'),
            'description': 'Текстовое содержимое статьи для индексации Google. '
                          'Заполняется автоматически из PDF или вручную.'
        }),
    )

    def has_seo_content(self, obj):
        return bool(obj.seo_content)
    has_seo_content.boolean = True
    has_seo_content.short_description = 'SEO'
