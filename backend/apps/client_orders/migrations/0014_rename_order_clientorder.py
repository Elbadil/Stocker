# Generated by Django 4.2.13 on 2024-11-13 10:09

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('client_orders', '0013_rename_orderstatus_clientorderstatus_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Order',
            new_name='ClientOrder',
        ),
    ]
