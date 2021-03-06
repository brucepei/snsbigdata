# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-25 05:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tbd', '0016_project_last_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='platform',
            field=models.CharField(choices=[('', '--select testcase--'), ('PHO', 'Phoenix XML'), ('VEG', 'Vega XML'), ('GAR', 'Garnet XML'), ('WPA', 'WPA Perl'), ('PAT', 'PAT Python')], default='', max_length=3),
        ),
        migrations.AlterUniqueTogether(
            name='testcase',
            unique_together=set([('project', 'name')]),
        ),
    ]
