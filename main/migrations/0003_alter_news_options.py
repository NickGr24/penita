# Generated by Django 5.1.3 on 2024-11-27 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_news_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='news',
            options={'verbose_name': 'Noutate', 'verbose_name_plural': 'Noutăți'},
        ),
    ]