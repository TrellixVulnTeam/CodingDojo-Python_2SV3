# Generated by Django 2.1.5 on 2019-02-19 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login_register', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.BinaryField(max_length=255),
        ),
    ]
