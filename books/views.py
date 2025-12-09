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

    # Check if user has access to this book
    user_has_access = book.has_user_purchased(request.user)

    # Show purchase button if book is paid and user doesn't have access
    show_purchase_button = book.is_paid and not user_has_access

    context = {
        'book': book,
        'user_has_access': user_has_access,
        'show_purchase_button': show_purchase_button,
    }

    return render(request, 'books/book_detail.html', context)
