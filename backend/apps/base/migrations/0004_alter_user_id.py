# Generated by Django 4.2.13 on 2024-06-26 15:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=uuid.UUID('e9b0c262-8ca0-4b3a-af79-c7399ac40b59'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
