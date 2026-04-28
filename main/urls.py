from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('google8a286773c4e6f9b1.html', views.google_verification, name='google_verification'),
    path('be563e094056a486e0ee315062904eff.txt', views.indexnow_key, name='indexnow_key'),

    # Reader API (cross-device sync + annotations)
    path('api/reading-progress/<str:content_type>/<int:content_id>/',
         views.reading_progress_get, name='reading_progress_get'),
    path('api/reading-progress/save/',
         views.reading_progress_save, name='reading_progress_save'),
    path('api/annotations/<str:content_type>/<int:content_id>/',
         views.annotations_list, name='annotations_list'),
    path('api/annotations/save/',
         views.annotation_create, name='annotation_create'),
    path('api/annotations/<int:annotation_id>/',
         views.annotation_delete, name='annotation_delete'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('register/', views.register, name='register'),
    path('tudor-osoianu/', views.osoianu, name='osoianu'),
    path('dinu-ostavciuc/', views.ostavciuc, name='ostavciuc'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
