# Generated by Django 5.1.4 on 2025-03-06 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminProfile', '0033_alter_orderitem_item_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='item_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELED', 'Canceled'), ('PARTIALLY_RETURNED', 'Partially Returned'), ('RETURNED', 'Returned')], default='PENDING', max_length=20),
        ),
    ]
