# Generated by Django 4.2.13 on 2024-12-09 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('supplier_orders', '0006_supplierordereditem_supplier'),
        ('inventory', '0022_item_in_inventory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='supplier_orders.supplier'),
        ),
    ]
