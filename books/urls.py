from django.urls import path
from . import views

urlpatterns = [
    path('books/', views.books_list, name='books_list'),
    path('books/<slug:slug>/', views.book_detail, name='book_detail'),
    path('books/<slug:slug>/pdf/', views.serve_book_pdf, name='serve_book_pdf'),
]
