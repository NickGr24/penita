from django.db import models
from django.utils.text import slugify

class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='news/', height_field=None, width_field=None, max_length=None)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Noutate'
        verbose_name_plural = 'Noutăți'


class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='news/gallery/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Imagine'
        verbose_name_plural = 'Imagini'

    def __str__(self):
        return f"Image for {self.news.title}"
