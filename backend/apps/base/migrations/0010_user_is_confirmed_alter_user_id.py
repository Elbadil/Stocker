# Generated by Django 4.2.13 on 2024-07-02 11:16

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_remove_user_is_confirmed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_confirmed',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=uuid.UUID('32171c03-716b-498b-8e9f-cf1585f450a5'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
