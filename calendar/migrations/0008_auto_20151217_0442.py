# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0007_auto_20151217_0441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userevent',
            name='google_json',
            field=models.TextField(default=b'NO JSON FOR THIS TASK'),
        ),
    ]
