# Generated by Django 4.2.13 on 2024-07-28 16:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_alter_variantoptions_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='posts',
        ),
        migrations.DeleteModel(
            name='Post',
        ),
    ]
