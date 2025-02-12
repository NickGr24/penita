from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Book

@login_required
def books_list(request):
    books = Book.objects.all()
    return render(request, 'books/books_list.html', {'books': books})
@login_required
def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    return render(request, 'books/book_detail.html', {'book': book})
