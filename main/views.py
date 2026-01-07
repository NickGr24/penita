from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse
from .models import News  

def homepage(request):
    news_list = News.objects.all().order_by('-id')
    return render(request, 'index.html', {'news_list': news_list})

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
    return render(request, 'osoianu.html')


def ostavciuc(request):
    return render(request, 'ostavciuc.html')


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
    """Генерация robots.txt"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Disallow admin and auth pages",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "",
        "# Sitemap",
        "Sitemap: https://penitadreptului.md/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def google_verification(request):
    """Google Search Console verification"""
    return HttpResponse("google-site-verification: google8a286773c4e6f9b1.html", content_type="text/html")