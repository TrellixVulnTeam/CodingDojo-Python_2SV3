# Generated by Django 2.1.5 on 2019-02-17 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dojo_ninjas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dojo',
            name='descr',
            field=models.TextField(null=True),
        ),
    ]