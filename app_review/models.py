import pickle
import base64

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models

from oauth2client.django_orm import FlowField
from oauth2client.django_orm import CredentialsField

from jsonfield import JSONField

class ReviewModel(models.Model):
    authenticated_user = models.ForeignKey(User, unique=False, null=False, default=None)
    last_day_reviewed = models.CharField(max_length="255", default=None)
    task_event_completion_per_day = JSONField()
    #To Store Below:
    #	-Date
    #	-Fraction for Task Hours Completed for Day
    #	-Fraction for Event Hours Completed for Day
    #	- '' Total for Day
