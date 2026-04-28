from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_news_created_at_news_updated_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadingProgress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('article', 'Article'), ('book', 'Book')], max_length=10)),
                ('content_id', models.PositiveIntegerField()),
                ('last_page', models.PositiveIntegerField(default=1)),
                ('last_read_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name='reading_progress',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Progres de citire',
                'verbose_name_plural': 'Progres de citire',
                'unique_together': {('user', 'content_type', 'content_id')},
                'indexes': [models.Index(fields=['user', 'content_type', 'content_id'], name='main_readin_user_id_efb8e6_idx')],
            },
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('article', 'Article'), ('book', 'Book')], max_length=10)),
                ('content_id', models.PositiveIntegerField()),
                ('page', models.PositiveIntegerField()),
                ('text_content', models.TextField()),
                ('color', models.CharField(
                    choices=[('yellow', 'Galben'), ('green', 'Verde'), ('blue', 'Albastru'), ('pink', 'Roz')],
                    default='yellow',
                    max_length=10,
                )),
                ('note', models.TextField(blank=True, default='', help_text='Заметка пользователя к выделению (опционально).')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name='annotations',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['page', 'created_at'],
                'verbose_name': 'Marcaj cu evidențiere',
                'verbose_name_plural': 'Marcaje cu evidențiere',
                'indexes': [models.Index(fields=['user', 'content_type', 'content_id', 'page'], name='main_annota_user_id_71b2f8_idx')],
            },
        ),
    ]
