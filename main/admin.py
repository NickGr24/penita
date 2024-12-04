from django.contrib import admin
from .models import News


@admin.register(News)
class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}