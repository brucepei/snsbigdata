# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-09 09:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0003_auto_20180407_1647'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ap',
            options={'ordering': ('ssid',)},
        ),
        migrations.AddField(
            model_name='ap',
            name='brand',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='ap',
            name='owner',
            field=models.CharField(default='', max_length=30),
        ),
    ]
