from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from django.template.defaultfilters import slugify

class Book(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    authors = (
        ('Tudor Osoianu', 'Tudor Osoianu'),
        ('Dinu Ostavciuc', 'Dinu Ostavciuc'),
        ('Tudor Osoianu, Dinu Ostavciuc', 'Tudor Osoianu, Dinu Ostavciuc')
    )
    author = models.CharField(max_length=200, choices=authors)
    file = models.FileField(upload_to='books/')
    slug = models.SlugField(unique=True, blank=True)

    # Timestamps for SEO (lastmod in sitemap)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # Payment fields
    is_paid = models.BooleanField(default=False, help_text='Check if this book requires payment')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text='Price in MDL (0 for free books)')
    preview_file = models.FileField(upload_to='books/previews/', null=True, blank=True, help_text='Optional preview file for paid books')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def has_user_purchased(self, user):
        """Check if user has purchased this book"""
        if not self.is_paid or self.price <= 0:
            return True  # Free books are always accessible
        if not user.is_authenticated:
            return False
        # Check if user has a successful payment for this book
        return self.payments.filter(user=user, status='OK').exists()
