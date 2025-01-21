from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Book
from .models import Subscription, PromoCode
from django.utils.timezone import now, timedelta
from .forms import SubscriptionForm

def subscribe(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            plan = form.cleaned_data['plan']
            promo_code = form.cleaned_data['promo_code']
            discount = 0

            if promo_code:
                try:
                    promo = PromoCode.objects.get(code=promo_code)
                    if promo.is_valid():
                        discount = promo.discount_percentage
                    else:
                        form.add_error('promo_code', 'Invalid or expired promo code.')
                except PromoCode.DoesNotExist:
                    form.add_error('promo_code', 'Promo code not found.')

            # Расчет финальной стоимости
            price = 9 if plan == 'monthly' else 99
            price -= price * discount / 100

            # Логика оплаты через платежный шлюз (примерный блок)
            # process_payment(price)

            # Сохраняем подписку
            Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'start_date': now(),
                    'end_date': now() + timedelta(days=30 if plan == 'monthly' else 365)
                }
            )

            return redirect('subscription_success')
    else:
        form = SubscriptionForm()

    return render(request, 'subscriptions/subscribe.html', {'form': form})

@login_required
def books_list(request):
    books = Book.objects.all()
    return render(request, 'books/books_list.html', {'books': books})
@login_required
def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    return render(request, 'books/book_detail.html', {'book': book})