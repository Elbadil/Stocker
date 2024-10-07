# Generated by Django 4.2.13 on 2024-07-01 14:46

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_alter_user_confirm_code_alter_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='confirm_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=uuid.UUID('0ece6355-4f31-4521-aeb0-0d5bde7a57d1'), editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]