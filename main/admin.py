from django.contrib import admin
from django.utils.html import format_html
from .models import News, NewsImage


class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 3
    fields = ('image', 'image_preview', 'order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = "Превью"


@admin.register(News)
class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    inlines = [NewsImageInline]
    list_display = ('title', 'slug')
    search_fields = ('title', 'content')