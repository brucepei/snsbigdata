# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-28 01:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tbd', '0020_auto_20160826_1601'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=80, unique=True)),
                ('is_default', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('project', 'name'),
            },
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pass_count', models.PositiveIntegerField(default=0)),
                ('fail_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ('build', 'host', 'testaction'),
            },
        ),
        migrations.AlterModelOptions(
            name='build',
            options={'ordering': ('project', '-create')},
        ),
        migrations.AlterModelOptions(
            name='crash',
            options={'ordering': ('build', '-create')},
        ),
        migrations.AlterModelOptions(
            name='host',
            options={'ordering': ('project', 'name')},
        ),
        migrations.AlterModelOptions(
            name='project',
            options={'ordering': ('-create',)},
        ),
        migrations.AlterModelOptions(
            name='testcase',
            options={'ordering': ('project', 'name')},
        ),
        migrations.AddField(
            model_name='build',
            name='is_stop',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='project',
            name='is_stop',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='jira',
            name='category',
            field=models.CharField(choices=[('', ''), ('OP', 'Open'), ('IN', 'Invalid'), ('WD', 'Withdraw'), ('CN', 'CNSS'), ('NC', 'Non-CNSS')], default='OP', max_length=2),
        ),
        migrations.AlterUniqueTogether(
            name='build',
            unique_together=set([('project', 'version')]),
        ),
        migrations.AddField(
            model_name='testresult',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tbd.Build', verbose_name='the related build'),
        ),
        migrations.AddField(
            model_name='testresult',
            name='host',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tbd.Host', verbose_name='the related host'),
        ),
        migrations.AddField(
            model_name='testresult',
            name='testaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tbd.TestAction', verbose_name='the related testaction'),
        ),
        migrations.AddField(
            model_name='testaction',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='tbd.Project', verbose_name='the related project'),
        ),
        migrations.AddField(
            model_name='testcase',
            name='testactions',
            field=models.ManyToManyField(to='tbd.TestAction'),
        ),
        migrations.AlterUniqueTogether(
            name='testresult',
            unique_together=set([('build', 'host', 'testaction')]),
        ),
        migrations.AlterUniqueTogether(
            name='testaction',
            unique_together=set([('project', 'name')]),
        ),
    ]
