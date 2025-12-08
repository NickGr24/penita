from django.urls import path
from . import views

urlpatterns = [
    path('payment/initiate/<int:book_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/success/<uuid:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/fail/<uuid:payment_id>/', views.payment_fail, name='payment_fail'),
    path('payment/history/', views.payment_history, name='payment_history'),
    path('payment/status/<uuid:payment_id>/', views.check_payment_status, name='check_payment_status'),
]