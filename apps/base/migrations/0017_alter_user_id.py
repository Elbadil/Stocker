# Generated by Django 4.2.13 on 2024-07-06 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0016_alter_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default='55ffc261-53dc-4964-a647-e1e453380a7c', editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
