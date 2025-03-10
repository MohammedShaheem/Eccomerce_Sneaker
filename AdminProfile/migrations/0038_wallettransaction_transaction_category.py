# Generated by Django 5.1.4 on 2025-03-06 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminProfile', '0037_order_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallettransaction',
            name='transaction_category',
            field=models.CharField(choices=[('ORDER_CANCELLATION', 'Order Cancellation'), ('ORDER_RETURN', 'Order Return')], default='WALLET_OPERATION', max_length=20),
        ),
    ]
