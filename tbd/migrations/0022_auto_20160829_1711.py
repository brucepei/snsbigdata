# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-29 09:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tbd', '0021_auto_20160828_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testaction',
            name='name',
            field=models.CharField(default='', max_length=80),
        ),
    ]
