# Generated by Django 4.2.13 on 2024-07-06 18:58

from django.db import migrations, models
import utils.tokens


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0017_alter_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=utils.tokens.Token.generate_uuid, editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
