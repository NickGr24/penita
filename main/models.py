from django.db import models
from django.utils.text import slugify
from .utils import convert_to_webp

class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='news/', null=True, blank=True, help_text='Главное изображение (опционально)')
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Convert image to WebP if present
        if self.image:
            self.image = convert_to_webp(self.image)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Noutate'
        verbose_name_plural = 'Noutăți'


class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='news/gallery/')
    order = models.PositiveIntegerField(default=0, help_text='Порядок отображения (0, 1, 2...)')

    def save(self, *args, **kwargs):
        # Convert image to WebP if present
        if self.image:
            self.image = convert_to_webp(self.image)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order']
        verbose_name = 'Imagine'
        verbose_name_plural = 'Imagini'

    def __str__(self):
        return f"Image for {self.news.title}"
