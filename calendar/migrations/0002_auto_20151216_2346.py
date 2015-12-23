# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calendar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userevent',
            name='authenticated_user',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userevent',
            name='task_name',
            field=models.CharField(default=b'None', max_length=300),
        ),
    ]
