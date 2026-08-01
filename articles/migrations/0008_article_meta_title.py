from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds a SEO-only title, separate from the article's own name.

    <title> and <h1> both rendered article.name, so tuning the search snippet
    would have renamed the authors' published work. This splits them: h1 keeps
    name, <head> uses meta_title when present.
    """

    dependencies = [
        ('articles', '0007_expand_slug_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='meta_title',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=120,
                help_text=(
                    'SEO-заголовок для <title> в выдаче Google. Если пусто — берётся name. '
                    'Заголовок статьи (H1) при этом НЕ меняется. '
                    'Нужен потому, что научное название статьи ("Arestul preventiv") '
                    'конкурирует с румынскими сайтами, а привязка к нормам РМ '
                    '("Arestul preventiv în procesul penal al RM (art. 308 CPP)") выводит '
                    'в молдавскую выдачу, где конкуренции почти нет. '
                    'Оптимальная длина — до 60 символов вместе с брендом.'
                ),
            ),
        ),
    ]
