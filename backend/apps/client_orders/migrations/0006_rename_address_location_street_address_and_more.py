# Generated by Django 4.2.13 on 2024-10-19 11:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('client_orders', '0005_remove_client_source_of_acquisition_client_source_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='location',
            old_name='address',
            new_name='street_address',
        ),
        migrations.AlterField(
            model_name='acquisitionsource',
            name='added_by',
            field=models.ForeignKey(blank=True, help_text='The user who added this acquisition source to the system', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_acquisition_sources', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='client',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='The user who initially registered this client', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_clients', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='location',
            name='added_by',
            field=models.ForeignKey(blank=True, help_text='The user who added this location to the system', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_locations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='The user who created this order', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_orders', to=settings.AUTH_USER_MODEL),
        ),
    ]
