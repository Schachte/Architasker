# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_new_events', '0004_userevent_current_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userevent',
            name='google_json',
            field=models.TextField(default=b'NO JSON FOR THIS TASK', unique=True),
        ),
    ]
