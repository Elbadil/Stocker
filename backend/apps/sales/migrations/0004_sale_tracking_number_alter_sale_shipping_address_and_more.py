# Generated by Django 4.2.13 on 2024-12-20 10:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client_orders', '0019_clientorder_payment_status_and_more'),
        ('sales', '0003_alter_sale_shipping_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='sale',
            name='shipping_address',
            field=models.ForeignKey(blank=True, help_text='The address to ship the items sold', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='client_orders.location'),
        ),
        migrations.AlterField(
            model_name='solditem',
            name='sale',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='sold_items', to='sales.sale'),
        ),
    ]
