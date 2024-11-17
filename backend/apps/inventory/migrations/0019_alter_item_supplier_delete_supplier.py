# Generated by Django 4.2.13 on 2024-11-17 13:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('supplier_orders', '0001_initial'),
        ('inventory', '0018_alter_category_options_alter_supplier_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='supplier_orders.supplier'),
        ),
        migrations.DeleteModel(
            name='Supplier',
        ),
    ]
