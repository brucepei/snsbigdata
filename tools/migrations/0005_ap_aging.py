# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-23 00:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0004_auto_20180409_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='ap',
            name='aging',
            field=models.IntegerField(default=0),
        ),
    ]
