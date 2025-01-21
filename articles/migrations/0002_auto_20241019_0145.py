# Generated by Django 3.2.12 on 2024-10-18 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='article',
            old_name='date',
            new_name='publication_date',
        ),
        migrations.AlterField(
            model_name='article',
            name='author',
            field=models.CharField(choices=[('Tudor Osoianu', 'Tudor Osoianu'), ('Dinu Ostavciuc', 'Dinu Ostavciuc'), ('Tudor Osoianu, Dinu Ostavciuc', 'Tudor Osoianu, Dinu Ostavciuc')], max_length=256),
        ),
    ]
