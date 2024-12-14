# Generated by Django 4.2.13 on 2024-12-11 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_alter_sale_client_alter_solditem_sale'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
    ]