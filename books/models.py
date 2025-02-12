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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
