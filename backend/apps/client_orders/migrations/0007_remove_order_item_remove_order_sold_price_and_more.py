# Generated by Django 4.2.13 on 2024-10-20 17:07

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.tokens


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0017_rename_variantoptions_variantoption_and_more'),
        ('client_orders', '0006_rename_address_location_street_address_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='item',
        ),
        migrations.RemoveField(
            model_name='order',
            name='sold_price',
        ),
        migrations.RemoveField(
            model_name='order',
            name='sold_quantity',
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.CreateModel(
            name='OrderedItem',
            fields=[
                ('id', models.UUIDField(default=utils.tokens.Token.generate_uuid, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ordered_quantity', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('ordered_price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.item')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_orders.order')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]