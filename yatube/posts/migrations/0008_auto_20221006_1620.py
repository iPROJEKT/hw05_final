# Generated by Django 2.2.6 on 2022-10-06 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220923_1426'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={},
        ),
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]