# Generated by Django 5.1 on 2024-08-23 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_alter_productgallery_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='on_promotion',
            field=models.BooleanField(default=False),
        ),
    ]
