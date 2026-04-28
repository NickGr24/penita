from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0006_expand_slug_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='cover',
            field=models.ImageField(
                upload_to='books/covers/',
                null=True,
                blank=True,
                help_text='Обложка книги (первая страница PDF или кастомное изображение).',
            ),
        ),
    ]
