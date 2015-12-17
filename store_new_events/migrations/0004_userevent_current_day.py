# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_new_events', '0003_auto_20151216_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='userevent',
            name='current_day',
            field=models.CharField(default=b'Monday', max_length=255),
        ),
    ]
