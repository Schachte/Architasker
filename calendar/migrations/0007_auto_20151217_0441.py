# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0006_userevent_special_event_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userevent',
            name='special_event_id',
            field=models.CharField(default=b'None', max_length=255),
        ),
    ]
