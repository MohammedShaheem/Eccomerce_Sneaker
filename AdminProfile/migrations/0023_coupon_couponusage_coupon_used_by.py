# Generated by Django 5.1.4 on 2025-02-24 20:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminProfile', '0022_alter_offer_valid_from_alter_offer_valid_till'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon_name', models.CharField(max_length=100, unique=True)),
                ('coupon_code', models.CharField(max_length=20, unique=True)),
                ('min_purchase_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount', models.DecimalField(decimal_places=2, max_digits=5)),
                ('discount_type', models.CharField(choices=[('fixed', 'Fixed'), ('percent', 'Percentage')], max_length=10)),
                ('valid_from', models.DateTimeField()),
                ('valid_till', models.DateTimeField()),
                ('max_uses', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='AdminProfile.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'coupon')},
            },
        ),
        migrations.AddField(
            model_name='coupon',
            name='used_by',
            field=models.ManyToManyField(related_name='used_coupons', through='AdminProfile.CouponUsage', to=settings.AUTH_USER_MODEL),
        ),
    ]
