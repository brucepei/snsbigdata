# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-20 11:22
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('tbd', '0003_auto_20160320_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='create',
            field=models.DateTimeField(default=datetime.datetime(2016, 3, 20, 11, 22, 20, 549000, tzinfo=utc)),
        ),
    ]
