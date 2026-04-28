from django.db import migrations, models
from django.utils.text import slugify


def regenerate_truncated_slugs(apps, schema_editor):
    """
    Перегенерирует slug'и, обрезанные дефолтным max_length=50.
    Старый slug сохраняется в legacy_slug — для 301-редиректа со старого URL.
    """
    Article = apps.get_model('articles', 'Article')
    for art in Article.objects.all():
        if not art.name:
            continue
        full_slug = slugify(art.name)
        if not full_slug:
            continue
        if len(art.slug) <= 50 and full_slug != art.slug and full_slug.startswith(art.slug):
            old_slug = art.slug
            candidate = full_slug
            counter = 2
            while Article.objects.filter(slug=candidate).exclude(pk=art.pk).exists():
                candidate = f"{full_slug}-{counter}"[:200]
                counter += 1
            art.legacy_slug = old_slug
            art.slug = candidate
            art.save(update_fields=['slug', 'legacy_slug'])


def reverse_truncate(apps, schema_editor):
    """
    Откат: вернуть исходный обрезанный slug из legacy_slug.
    """
    Article = apps.get_model('articles', 'Article')
    for art in Article.objects.exclude(legacy_slug__isnull=True).exclude(legacy_slug=''):
        art.slug = art.legacy_slug
        art.legacy_slug = None
        art.save(update_fields=['slug', 'legacy_slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0006_article_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=models.SlugField(max_length=200, unique=True),
        ),
        migrations.AddField(
            model_name='article',
            name='legacy_slug',
            field=models.SlugField(
                max_length=200,
                blank=True,
                null=True,
                db_index=True,
                help_text='Старый slug, если URL был изменён — используется для 301-редиректа со старого URL на новый (SEO).',
            ),
        ),
        migrations.RunPython(regenerate_truncated_slugs, reverse_truncate),
    ]
