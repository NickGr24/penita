from django.contrib import admin
from .models import Book, Subscription, PromoCode

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Subscription)
admin.site.register(PromoCode)