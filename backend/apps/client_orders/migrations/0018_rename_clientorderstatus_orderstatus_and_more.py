# Generated by Django 4.2.13 on 2024-11-17 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier_orders', '0002_supplierorderstatus_supplierorder_created_by_and_more'),
        ('client_orders', '0017_alter_clientorder_created_by'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ClientOrderStatus',
            new_name='OrderStatus',
        ),
        migrations.RenameField(
            model_name='clientorder',
            old_name='status',
            new_name='delivery_status',
        ),
        migrations.AddField(
            model_name='clientorder',
            name='tracking_number',
            field=models.CharField(blank=True, help_text='Tracking number for the shipment', max_length=50, null=True),
        ),
    ]
