# Generated by Django 5.1.4 on 2025-02-20 07:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminProfile', '0011_remove_producttable_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product_images_table',
            name='product',
        ),
        migrations.AddField(
            model_name='product_images_table',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='AdminProfile.variancetable'),
        ),
    ]
