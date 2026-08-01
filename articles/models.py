from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    CATEGORY_CHOICES = (
        ('procedura_penala', _('Criminal procedure')),
        ('criminalistica', _('Forensics')),
        ('alte_stiinte', _('Other sciences')),
    )
    authors = (
        ('Tudor Osoianu', 'Tudor Osoianu'),
        ('Dinu Ostavciuc', 'Dinu Ostavciuc'),
        ('Tudor Osoianu, Dinu Ostavciuc', 'Tudor Osoianu, Dinu Ostavciuc'),
	('Tudor Osoianu, Dumitru Calendari', 'Tudor Osoianu, Dumitru Calendari'),
    )
    name = models.CharField(max_length=256)
    description = models.TextField(max_length=500, blank=True, null=True)
    file = models.FileField(upload_to='files/articles')
    publication_date = models.DateField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True,
        help_text='Последнее обновление статьи (для sitemap lastmod, сигналит Google о recrawl)')
    author = models.CharField(max_length=256, choices=authors)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    legacy_slug = models.SlugField(max_length=200, blank=True, null=True, db_index=True,
        help_text='Старый slug, если URL был изменён — используется для 301-редиректа со старого URL на новый (SEO).')
    
    # SEO fields - текстовое содержимое для индексации Google
    seo_content = models.TextField(blank=True, null=True,
        help_text="HTML версия статьи для SEO (будет видна Google)")
    excerpt = models.TextField(max_length=500, blank=True, null=True,
        help_text="Краткий отрывок для превью на странице")
    meta_title = models.CharField(max_length=120, blank=True, null=True,
        help_text=(
            'SEO-заголовок для <title> в выдаче Google. Если пусто — берётся name. '
            'Заголовок статьи (H1) при этом НЕ меняется. '
            'Нужен потому, что научное название статьи ("Arestul preventiv") '
            'конкурирует с румынскими сайтами, а привязка к нормам РМ '
            '("Arestul preventiv în procesul penal al RM (art. 308 CPP)") выводит '
            'в молдавскую выдачу, где конкуренции почти нет. '
            'Оптимальная длина — до 60 символов вместе с брендом.'
        ))

    @property
    def seo_title(self):
        """Title for <head>; falls back to the article's own name."""
        return self.meta_title or self.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Articol'
        verbose_name_plural = 'Articole'
