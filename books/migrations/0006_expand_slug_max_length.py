from django.db import migrations, models
from django.template.defaultfilters import slugify


def regenerate_truncated_slugs(apps, schema_editor):
    """
    Перегенерирует slug'и, обрезанные дефолтным max_length=50.
    Старый slug сохраняется в legacy_slug — для 301-редиректа со старого URL.
    """
    Book = apps.get_model('books', 'Book')
    for book in Book.objects.all():
        if not book.title:
            continue
        full_slug = slugify(book.title)
        if not full_slug:
            continue
        if len(book.slug or '') <= 50 and full_slug != book.slug and full_slug.startswith(book.slug or ''):
            old_slug = book.slug
            candidate = full_slug
            counter = 2
            while Book.objects.filter(slug=candidate).exclude(pk=book.pk).exists():
                candidate = f"{full_slug}-{counter}"[:200]
                counter += 1
            book.legacy_slug = old_slug
            book.slug = candidate
            book.save(update_fields=['slug', 'legacy_slug'])


def reverse_truncate(apps, schema_editor):
    Book = apps.get_model('books', 'Book')
    for book in Book.objects.exclude(legacy_slug__isnull=True).exclude(legacy_slug=''):
        book.slug = book.legacy_slug
        book.legacy_slug = None
        book.save(update_fields=['slug', 'legacy_slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0005_book_seo_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='slug',
            field=models.SlugField(max_length=200, unique=True, blank=True),
        ),
        migrations.AddField(
            model_name='book',
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
