# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0005_auto_20151217_0437'),
    ]

    operations = [
        migrations.AddField(
            model_name='userevent',
            name='special_event_id',
            field=models.CharField(default=b'None', unique=True, max_length=255),
        ),
    ]
