# Generated by Django 4.2.13 on 2024-11-17 16:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client_orders', '0019_clientorder_payment_status_and_more'),
        ('supplier_orders', '0003_remove_supplierorder_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplierorder',
            name='delivery_status',
            field=models.ForeignKey(blank=True, default='8ccdc2f8-1d6e-489f-81cf-7df3c4fce245', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_delivery_status', to='client_orders.orderstatus'),
        ),
        migrations.AlterField(
            model_name='supplierorder',
            name='payment_status',
            field=models.ForeignKey(blank=True, default='8ccdc2f8-1d6e-489f-81cf-7df3c4fce245', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_payment_status', to='client_orders.orderstatus'),
        ),
    ]
