# Generated manually - fix three_ds field length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='three_ds',
            field=models.CharField(blank=True, help_text='3D Secure status', max_length=20, null=True),
        ),
    ]
