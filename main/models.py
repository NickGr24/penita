from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from .utils import convert_to_webp


# Type tags for ReadingProgress / Annotation — not FK to Article/Book
# чтобы не ловить циркулярный импорт; целостность контролируем в API.
CONTENT_TYPE_CHOICES = (
    ('article', 'Article'),
    ('book', 'Book'),
)


class ReadingProgress(models.Model):
    """Per-user, per-document last-read page (cross-device sync)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    content_id = models.PositiveIntegerField()
    last_page = models.PositiveIntegerField(default=1)
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'content_type', 'content_id')
        indexes = [models.Index(fields=['user', 'content_type', 'content_id'])]
        verbose_name = 'Progres de citire'
        verbose_name_plural = 'Progres de citire'

    def __str__(self):
        return f"{self.user} — {self.content_type}#{self.content_id} pag.{self.last_page}"


class Annotation(models.Model):
    """User-created highlight on a PDF page (text content + page only — no exact coords)."""
    COLOR_CHOICES = (
        ('yellow', 'Galben'),
        ('green', 'Verde'),
        ('blue', 'Albastru'),
        ('pink', 'Roz'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    content_id = models.PositiveIntegerField()
    page = models.PositiveIntegerField()
    # Хранится текст выделенного фрагмента — на render находим matching span'ы и подсвечиваем.
    text_content = models.TextField()
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='yellow')
    note = models.TextField(blank=True, default='', help_text='Заметка пользователя к выделению (опционально).')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page', 'created_at']
        indexes = [models.Index(fields=['user', 'content_type', 'content_id', 'page'])]
        verbose_name = 'Marcaj cu evidențiere'
        verbose_name_plural = 'Marcaje cu evidențiere'

    def __str__(self):
        return f"{self.user} — {self.content_type}#{self.content_id} pag.{self.page}: {self.text_content[:40]}"

class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='news/', null=True, blank=True, help_text='Главное изображение (опционально)')
    slug = models.SlugField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

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
