# Generated by Django 4.2.13 on 2024-07-09 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_delete_postdescription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=300, unique=True),
        ),
    ]
