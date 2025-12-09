from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_paid', 'price', 'slug')
    list_filter = ('is_paid', 'author')
    list_editable = ('is_paid', 'price')
    search_fields = ('title', 'description', 'author')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description')
        }),
        ('Files', {
            'fields': ('file', 'preview_file')
        }),
        ('Payment Settings', {
            'fields': ('is_paid', 'price'),
            'description': 'Set pricing for this book. If is_paid is checked, users must pay to access.'
        }),
    )

