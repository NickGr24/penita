from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from django.template.defaultfilters import slugify

class Subscription(models.Model):
    PLAN_CHOICES = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES)
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.end_date:
            if self.plan == 'monthly':
                self.end_date = self.start_date + timedelta(days=30)
            elif self.plan == 'yearly':
                self.end_date = self.start_date + timedelta(days=365)
        super().save(*args, **kwargs)

    def is_active(self):
        return self.end_date >= now()

    def __str__(self):
        return f"{self.user.username} - {self.plan.capitalize()} Subscription"

class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.PositiveIntegerField()  # Скидка в процентах (например, 10 для 10%)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField()

    def is_valid(self):
        return self.is_active and self.expiration_date >= now()

    def __str__(self):
        return self.code

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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
