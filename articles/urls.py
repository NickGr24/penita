from django.urls import path
from . import views

urlpatterns = [
    path('articles/', views.articles, name='articles'),
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
    path('articles/<slug:slug>/pdf/', views.serve_article_pdf, name='serve_article_pdf'),
]