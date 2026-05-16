from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
import json
from .models import News, ReadingProgress, Annotation, CONTENT_TYPE_CHOICES
from articles.models import Article
from books.models import Book


VALID_CONTENT_TYPES = {c[0] for c in CONTENT_TYPE_CHOICES}


def _validate_content(content_type, content_id):
    """Проверяем что content_type валидный и запись существует."""
    if content_type not in VALID_CONTENT_TYPES:
        return None, "Invalid content_type"
    Model = Article if content_type == 'article' else Book
    try:
        obj = Model.objects.get(pk=int(content_id))
    except (Model.DoesNotExist, ValueError, TypeError):
        return None, "Content not found"
    return obj, None

def homepage(request):
    news_list = News.objects.all().order_by('-id')
    latest_articles = Article.objects.all().order_by('-publication_date')[:6]
    featured_books = Book.objects.all().order_by('-created_at')[:4]
    return render(request, 'index.html', {
        'news_list': news_list,
        'latest_articles': latest_articles,
        'featured_books': featured_books,
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Contul creat pentru {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'user/register.html', {'form': form})

def osoianu(request):
    articles = Article.objects.filter(author__icontains='Tudor Osoianu').order_by('-publication_date')
    books = Book.objects.filter(author__icontains='Tudor Osoianu').order_by('-created_at')
    return render(request, 'osoianu.html', {'articles': articles, 'books': books})


def ostavciuc(request):
    articles = Article.objects.filter(author__icontains='Dinu Ostavciuc').order_by('-publication_date')
    books = Book.objects.filter(author__icontains='Dinu Ostavciuc').order_by('-created_at')
    return render(request, 'ostavciuc.html', {'articles': articles, 'books': books})


def news_detail(request, slug):
    news = get_object_or_404(News, slug=slug)
    return render(request, 'news_detail.html', {'news': news})

def login(request):
    return render(request, 'accounts/socialaccount/login.html')

def terms_and_conditions(request):
    return render(request, 'policies/terms.html')

def privacy_policy(request):
    return render(request, 'policies/privacy.html')


def robots_txt(request):
    """Генерация robots.txt с оптимизацией для SEO"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /static/",
        "Allow: /media/",
        "",
        "# Disallow admin and auth pages",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /accounts/signup/",
        "Disallow: /accounts/login/",
        "Disallow: /accounts/password/",
        "Disallow: /accounts/email/",
        "Disallow: /accounts/social/",
        "",
        "# Disallow payment pages",
        "Disallow: /payments/",
        "Disallow: /confirm-payment/",
        "Disallow: /payment-success/",
        "Disallow: /payment-fail/",
        "",
        "# Block aggressive bots",
        "User-agent: MJ12bot",
        "Disallow: /",
        "",
        "User-agent: AhrefsBot",
        "Crawl-delay: 10",
        "",
        "# Main domain",
        "Host: penitadreptului.md",
        "",
        "# Sitemap",
        "Sitemap: https://penitadreptului.md/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def google_verification(request):
    """Google Search Console verification"""
    return HttpResponse("google-site-verification: google8a286773c4e6f9b1.html", content_type="text/html")


# IndexNow protocol key (Bing/Yandex). См. https://www.indexnow.org/
# Файл должен быть доступен по https://penitadreptului.md/<key>.txt и
# содержать тот же ключ — это подтверждает, что мы владеем сайтом.
INDEXNOW_KEY = "be563e094056a486e0ee315062904eff"


def indexnow_key(request):
    """Verifies site ownership for IndexNow protocol (Bing, Yandex)."""
    return HttpResponse(INDEXNOW_KEY, content_type="text/plain")


# ============================================================
# Reader API: cross-device reading progress + annotations
# ============================================================
# CSRF: Django default cookie-based; JS читает csrftoken cookie и шлёт в X-CSRFToken header.
# Auth: login_required отдаёт redirect на /accounts/login/. Для XHR это плохо — клиент
# должен видеть 401, чтобы fall back на localStorage. Поэтому свой mini-decorator.

def _ajax_login_required(view):
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'authentication_required'}, status=401)
        return view(request, *args, **kwargs)
    return wrapped


@require_http_methods(["GET"])
@_ajax_login_required
def reading_progress_get(request, content_type, content_id):
    obj, err = _validate_content(content_type, content_id)
    if err:
        return JsonResponse({'error': err}, status=400)
    try:
        rp = ReadingProgress.objects.get(user=request.user, content_type=content_type, content_id=obj.pk)
        return JsonResponse({'page': rp.last_page, 'last_read_at': rp.last_read_at.isoformat()})
    except ReadingProgress.DoesNotExist:
        return JsonResponse({'page': None})


@require_http_methods(["POST"])
@_ajax_login_required
def reading_progress_save(request):
    try:
        data = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    obj, err = _validate_content(data.get('type'), data.get('id'))
    if err:
        return JsonResponse({'error': err}, status=400)
    try:
        page = int(data.get('page', 1))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid page'}, status=400)
    if page < 1:
        page = 1
    ReadingProgress.objects.update_or_create(
        user=request.user,
        content_type=data['type'],
        content_id=obj.pk,
        defaults={'last_page': page},
    )
    return JsonResponse({'ok': True, 'page': page})


@require_http_methods(["GET"])
@_ajax_login_required
def annotations_list(request, content_type, content_id):
    obj, err = _validate_content(content_type, content_id)
    if err:
        return JsonResponse({'error': err}, status=400)
    qs = Annotation.objects.filter(user=request.user, content_type=content_type, content_id=obj.pk)
    return JsonResponse({
        'annotations': [
            {'id': a.id, 'page': a.page, 'text': a.text_content, 'color': a.color, 'note': a.note,
             'created_at': a.created_at.isoformat()}
            for a in qs
        ]
    })


@require_http_methods(["POST"])
@_ajax_login_required
def annotation_create(request):
    try:
        data = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    obj, err = _validate_content(data.get('type'), data.get('id'))
    if err:
        return JsonResponse({'error': err}, status=400)
    text = (data.get('text') or '').strip()
    if not text:
        return JsonResponse({'error': 'text required'}, status=400)
    try:
        page = int(data.get('page', 1))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid page'}, status=400)
    color = data.get('color', 'yellow')
    if color not in {c[0] for c in Annotation.COLOR_CHOICES}:
        color = 'yellow'
    a = Annotation.objects.create(
        user=request.user,
        content_type=data['type'],
        content_id=obj.pk,
        page=max(1, page),
        text_content=text[:5000],  # safety cap
        color=color,
        note=(data.get('note') or '')[:1000],
    )
    return JsonResponse({'ok': True, 'id': a.id, 'page': a.page, 'text': a.text_content,
                         'color': a.color, 'note': a.note})


@require_http_methods(["DELETE"])
@_ajax_login_required
def annotation_delete(request, annotation_id):
    try:
        a = Annotation.objects.get(pk=annotation_id, user=request.user)
    except Annotation.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    a.delete()
    return JsonResponse({'ok': True})


# === Personal account dashboard ===

@login_required
def account_dashboard(request):
    """User's personal area: purchased books + reading progress, profile, payment history."""
    from payments.models import Payment

    successful = (
        Payment.objects
        .filter(user=request.user, status='OK')
        .select_related('book')
        .order_by('-paid_at', '-created_at')
    )
    seen_book_ids = set()
    purchased_books = []
    for p in successful:
        if p.book_id in seen_book_ids:
            continue
        seen_book_ids.add(p.book_id)
        purchased_books.append(p.book)

    progress_map = {
        rp.content_id: rp
        for rp in ReadingProgress.objects.filter(
            user=request.user,
            content_type='book',
            content_id__in=seen_book_ids,
        )
    }

    books_with_progress = []
    for book in purchased_books:
        rp = progress_map.get(book.id)
        books_with_progress.append({
            'book': book,
            'last_page': rp.last_page if rp else None,
            'last_read_at': rp.last_read_at if rp else None,
        })

    payment_history = (
        Payment.objects
        .filter(user=request.user)
        .select_related('book')
        .order_by('-created_at')[:50]
    )

    return render(request, 'account/dashboard.html', {
        'books_with_progress': books_with_progress,
        'payment_history': payment_history,
    })


@login_required
@require_http_methods(["GET", "POST"])
def account_delete(request):
    """GDPR right to be forgotten: confirm and permanently delete the user account."""
    from django.contrib.auth import logout

    if request.method == 'POST':
        typed = (request.POST.get('confirm_email') or '').strip().lower()
        if typed != (request.user.email or '').lower():
            messages.error(request, _("The email you typed does not match your account email."))
            return render(request, 'account/account_delete.html')

        user = request.user
        logout(request)
        user.delete()
        messages.success(request, _("Your account has been permanently deleted."))
        return redirect('home')

    return render(request, 'account/account_delete.html')