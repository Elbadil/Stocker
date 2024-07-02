# Generated by Django 4.2.13 on 2024-07-01 13:24

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_user_confirm_code_user_is_confirmed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='confirm_code',
            field=models.CharField(max_length=6, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=uuid.UUID('de562765-9d05-4fd0-9799-1c9d9c57e7fc'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
