# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-26 06:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tbd', '0018_auto_20160825_1930'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jira',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='testcase',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
    ]
