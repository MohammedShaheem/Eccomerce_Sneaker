# Generated by Django 5.1.4 on 2025-03-06 05:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminProfile', '0035_alter_order_order_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='shipping_address',
        ),
        migrations.CreateModel(
            name='OrderAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=254)),
                ('address_type', models.TextField()),
                ('address_line2', models.CharField(blank=True, max_length=255, null=True)),
                ('house_name', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('pincode', models.CharField(max_length=10)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order_address', to='AdminProfile.order')),
            ],
            options={
                'verbose_name': 'Order Address',
                'verbose_name_plural': 'Order Addresses',
                'db_table': 'OrderAdress',
            },
        ),
    ]
