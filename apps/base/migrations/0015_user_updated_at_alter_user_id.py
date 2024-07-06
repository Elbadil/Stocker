# Generated by Django 4.2.13 on 2024-07-06 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_alter_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default='eee67982-64a9-4fb9-9bc7-10d37c69c131', editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
