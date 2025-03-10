# Generated by Django 4.2.13 on 2024-10-24 14:13

from django.db import migrations, models
import django.db.models.deletion
import utils.tokens


class Migration(migrations.Migration):

    dependencies = [
        ('client_orders', '0009_ordereditem_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.UUIDField(default=utils.tokens.Token.generate_uuid, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='location',
            name='region',
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.ForeignKey(blank=True, default='8ccdc2f8-1d6e-489f-81cf-7df3c4fce245', null=True, on_delete=django.db.models.deletion.SET_NULL, to='client_orders.orderstatus'),
        ),
        migrations.AlterField(
            model_name='ordereditem',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ordered_items', to='client_orders.order'),
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.UUIDField(default=utils.tokens.Token.generate_uuid, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='client_orders.country')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='location',
            name='city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_orders.city'),
        ),
        migrations.AlterField(
            model_name='location',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_orders.country'),
        ),
    ]
