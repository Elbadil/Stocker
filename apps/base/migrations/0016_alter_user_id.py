# Generated by Django 4.2.13 on 2024-07-06 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_user_updated_at_alter_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default='789bbb81-cb01-4ec7-9cc3-375d8ac1feb1', editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
