# Generated by Django 5.1.4 on 2025-03-05 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminProfile', '0030_alter_orderitem_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='cancelation_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='is_canceled',
            field=models.BooleanField(default=False),
        ),
    ]
