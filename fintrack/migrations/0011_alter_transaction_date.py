# Generated by Django 5.0.4 on 2024-12-23 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fintrack', '0010_alter_recurrenceperiod_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='date',
            field=models.DateField(),
        ),
    ]
