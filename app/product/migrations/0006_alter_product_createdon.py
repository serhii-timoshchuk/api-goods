# Generated by Django 4.1 on 2022-08-30 08:36

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_product_createdon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='createdon',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
