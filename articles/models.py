from django.db import models
from django.utils.text import slugify

class Article(models.Model):
    CATEGORY_CHOICES = (
        ('procedura_penala', 'Procedura Penală'),
        ('criminalistica', 'Criminalistica'),
        ('alte_stiinte', 'Alte Științe'),
    )
    authors = (
        ('Tudor Osoianu', 'Tudor Osoianu'),
        ('Dinu Ostavciuc', 'Dinu Ostavciuc'),
        ('Tudor Osoianu, Dinu Ostavciuc', 'Tudor Osoianu, Dinu Ostavciuc')
    )
    name = models.CharField(max_length=256)
    description = models.TextField(max_length=500, blank=True, null=True)
    file = models.FileField(upload_to='files/articles')
    publication_date = models.DateField(auto_now_add=True, blank=True, null=True)
    author = models.CharField(max_length=256, choices=authors)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    slug = models.SlugField()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Articol'
        verbose_name_plural = 'Articole'