from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from books.models import Book
from .models import Payment
from .services import MAIBPaymentService
import json
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def initiate_payment(request, book_id):
    """Initiate a payment for a book"""
    book = get_object_or_404(Book, id=book_id)
    
    # Check if book requires payment
    if not book.is_paid or book.price <= 0:
        messages.info(request, "This book is free!")
        return redirect('book_detail', slug=book.slug)
    
    # Check if user already purchased this book
    if book.has_user_purchased(request.user):
        messages.info(request, "You already have access to this book!")
        return redirect('book_detail', slug=book.slug)
    
    if request.method == 'POST':
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            book=book,
            amount=book.price,
            currency='MDL',
            description=f"Payment for book: {book.title}",
            client_ip=get_client_ip(request)
        )
        
        # Initialize MAIB service
        service = MAIBPaymentService(test_mode=True)  # Use test mode for now
        
        # Initiate payment with MAIB
        success, result = service.initiate_payment(payment, request)

        if success:
            # Redirect to MAIB payment page
            pay_url = result.get('payUrl')
            if pay_url:
                logger.info(f"Redirecting to MAIB payment page: {pay_url}")
                return HttpResponseRedirect(pay_url)
            else:
                logger.error("Payment initiation succeeded but no payUrl received")
                messages.error(request, "Failed to get payment URL from MAIB")
                payment.status = 'FAIL'
                payment.save()
        else:
            error_msg = result.get('error', 'Payment initiation failed')
            logger.error(f"Payment initiation failed: {error_msg}")
            messages.error(request, f"Ошибка оплаты: {error_msg}")
            payment.status = 'FAIL'
            payment.save()

        return redirect('book_detail', slug=book.slug)
    
    # GET request - show payment confirmation page
    context = {
        'book': book,
        'amount': book.price,
        'currency': 'MDL'
    }
    return render(request, 'payments/confirm_payment.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    """Handle callback from MAIB with payment result"""
    try:
        # Parse callback data
        if request.content_type == 'application/json':
            callback_data = json.loads(request.body)
        else:
            callback_data = request.POST.dict()
        
        logger.info(f"Received callback: {callback_data}")
        
        # Process callback
        service = MAIBPaymentService(test_mode=True)
        success = service.process_callback(callback_data)
        
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error'}, status=400)
            
    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def payment_success(request, payment_id):
    """Show success page after payment"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    # Check payment status from database
    if payment.status == 'OK':
        messages.success(request, f"Payment successful! You can now access {payment.book.title}")
    else:
        # Try to check status from MAIB
        service = MAIBPaymentService(test_mode=True)
        status_info = service.get_payment_status(payment)
        
        if status_info and status_info.get('status') == 'OK':
            payment.status = 'OK'
            payment.save()
            messages.success(request, f"Payment successful! You can now access {payment.book.title}")
        else:
            messages.warning(request, "Payment is being processed. Please check back later.")
    
    context = {
        'payment': payment,
        'book': payment.book
    }
    return render(request, 'payments/payment_success.html', context)


@login_required
def payment_fail(request, payment_id):
    """Show failure page after payment"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status == 'PENDING':
        payment.status = 'FAIL'
        payment.save()
    
    messages.error(request, "Payment failed or was cancelled. Please try again.")
    
    context = {
        'payment': payment,
        'book': payment.book
    }
    return render(request, 'payments/payment_fail.html', context)


@login_required
def payment_history(request):
    """Show user's payment history"""
    payments = Payment.objects.filter(user=request.user).select_related('book')
    
    context = {
        'payments': payments
    }
    return render(request, 'payments/payment_history.html', context)


@login_required
def check_payment_status(request, payment_id):
    """Check payment status via AJAX"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    # Check if status needs updating
    if payment.status == 'PENDING':
        service = MAIBPaymentService(test_mode=True)
        status_info = service.get_payment_status(payment)
        
        if status_info:
            payment.status = status_info.get('status', 'PENDING')
            if payment.status == 'OK':
                payment.paid_at = timezone.now()
            payment.save()
    
    return JsonResponse({
        'status': payment.status,
        'is_successful': payment.is_successful()
    })


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'