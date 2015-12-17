# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_new_events', '0009_auto_20151217_0448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userevent',
            name='current_day',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
