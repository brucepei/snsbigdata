# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-11-04 04:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tbd', '0024_testresult_last_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='jira',
            name='cr_id',
            field=models.CharField(default='', max_length=20),
        ),
    ]