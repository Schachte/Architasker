# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0002_auto_20151216_2346'),
    ]

    operations = [
        migrations.AddField(
            model_name='userevent',
            name='color',
            field=models.CharField(default=b'None', max_length=255),
        ),
        migrations.AddField(
            model_name='userevent',
            name='end_time',
            field=models.CharField(default=b'None', max_length=255),
        ),
        migrations.AddField(
            model_name='userevent',
            name='google_json',
            field=models.TextField(default=b'NO JSON FOR THIS TASK'),
        ),
        migrations.AddField(
            model_name='userevent',
            name='start_time',
            field=models.CharField(default=b'None', max_length=255),
        ),
        migrations.AddField(
            model_name='userevent',
            name='url',
            field=models.CharField(default=b'None', max_length=255),
        ),
    ]
