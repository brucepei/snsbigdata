# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-23 00:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0005_ap_aging'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ap',
            name='aging',
            field=models.DateTimeField(blank=True),
        ),
    ]