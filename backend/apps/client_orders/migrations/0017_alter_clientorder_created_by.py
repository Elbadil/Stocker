# Generated by Django 4.2.13 on 2024-11-17 14:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('client_orders', '0016_alter_clientorder_client_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientorder',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='The user who created this order', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_client_orders', to=settings.AUTH_USER_MODEL),
        ),
    ]
