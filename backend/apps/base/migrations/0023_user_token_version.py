# Generated by Django 4.2.13 on 2024-09-19 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0022_remove_user_confirm_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='token_version',
            field=models.IntegerField(default=1),
        ),
    ]