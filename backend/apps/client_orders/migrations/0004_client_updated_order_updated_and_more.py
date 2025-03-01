# Generated by Django 4.2.13 on 2024-10-18 18:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('client_orders', '0003_rename_user_acquisitionsource_added_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='updated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='updated',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='acquisitionsource',
            name='added_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_acquisition_sources', to=settings.AUTH_USER_MODEL),
        ),
    ]
