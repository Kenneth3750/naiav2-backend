# Generated by Django 5.1.5 on 2025-03-04 20:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        ('roles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='rol',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='roles.roles'),
        ),
        migrations.DeleteModel(
            name='Roles',
        ),
    ]
