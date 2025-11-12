from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('contacts/', views.contacts, name='contacts'),
    path('register/', views.register, name='register'),
    path('tudor-osoianu/', views.osoianu, name='osoianu'),
    path('dinu-ostavciuc/', views.ostavciuc, name='ostavciuc'), 
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),  
]
