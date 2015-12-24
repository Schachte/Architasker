import pickle
import base64

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models

from oauth2client.django_orm import FlowField
from oauth2client.django_orm import CredentialsField


class CredentialsModel(models.Model):
  id = models.ForeignKey(User, primary_key=True)
  credential = CredentialsField()


class CredentialsAdmin(admin.ModelAdmin):
    pass


admin.site.register(CredentialsModel, CredentialsAdmin)


class UserEvent(models.Model):
    authenticated_user = models.ForeignKey(User, unique=False, null=False, default=None)
    task_name = models.CharField(max_length=300, unique=False, default='None')
    is_google_task = models.BooleanField(default=False, unique=False)
    google_json = models.TextField(default='NO JSON FOR THIS TASK')
    start_time = models.CharField(max_length=255, default='None')
    end_time = models.CharField(max_length=255, default='None')
    url = models.CharField(max_length=255, default='None')
    color = models.CharField(max_length=255, default='None')
    current_day = models.CharField(max_length=255, null=True) #Maybe need to change the default day on this field
    special_event_id = models.CharField(max_length=255, default="None", unique=True) #Make sure not duplicate events get stored in the DB
