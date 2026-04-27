from django.db import migrations, models
from django.utils import timezone


def backfill_updated_at(apps, schema_editor):
    """
    Заполняет updated_at для всех существующих статей текущим временем.
    Это нужно чтобы sitemap.xml сразу же содержал свежий lastmod
    и Google поставил статьи в очередь recrawl (для применения новых
    excerpt'ов и meta description'ов).
    """
    Article = apps.get_model('articles', 'Article')
    Article.objects.update(updated_at=timezone.now())


def reverse_backfill(apps, schema_editor):
    # No-op: при отмене миграции AddField откатится автоматически,
    # данные потеряются вместе с колонкой.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0005_merge_0004_article_slug_unique_0004_seed_seo_excerpts'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                null=True,
                help_text='Последнее обновление статьи (для sitemap lastmod, сигналит Google о recrawl)',
            ),
        ),
        migrations.RunPython(backfill_updated_at, reverse_backfill),
    ]
