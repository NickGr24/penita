import logging
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _format_money(amount):
    if amount is None:
        return '—'
    return f"{Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)} MDL"


def send_purchase_notification(payment):
    """
    Send admin notification email after a successful book purchase.

    Никогда не raise — MAIB callback должен вернуть 200 даже если SMTP лёг,
    иначе MAIB будет ретраить и мы получим дубли уведомлений + дубли логики.
    """
    recipients = settings.PURCHASE_NOTIFICATION_RECIPIENTS
    if not recipients:
        logger.warning('PURCHASE_NOTIFICATION_RECIPIENTS не настроен — skip notification.')
        return

    amount = Decimal(payment.amount)
    commission = (amount * settings.MAIB_COMMISSION_RATE).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    net = (amount - commission).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    ctx = {
        'payment': payment,
        'book': payment.book,
        'user': payment.user,
        'user_email': payment.user.email or '—',
        'user_full_name': payment.user.get_full_name() or payment.user.username,
        'amount_str': _format_money(amount),
        'commission_str': _format_money(commission),
        'commission_percent': (settings.MAIB_COMMISSION_RATE * 100).quantize(Decimal('0.01')),
        'net_str': _format_money(net),
        'paid_at': payment.paid_at or timezone.now(),
        'currency': payment.currency,
    }
    subject = f"[Penița Dreptului] Vânzare nouă: {payment.book.title} — {ctx['amount_str']}"

    try:
        text_body = render_to_string('payments/email/purchase_notification.txt', ctx)
        html_body = render_to_string('payments/email/purchase_notification.html', ctx)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info(
            'Purchase notification sent for payment %s (book=%s, recipients=%s)',
            payment.pay_id, payment.book.id, recipients,
        )
    except Exception:
        logger.exception('Failed to send purchase notification for payment %s', payment.pay_id)
