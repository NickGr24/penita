from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import News  

def homepage(request):
    news_list = News.objects.all()
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

def contacts(request):
    return render(request, 'contacts.html')

def terms_and_conditions(request):
    return render(request, 'policies/terms.html')

def privacy_policy(request):
    return render(request, 'policies/privacy.html')