from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User

class User_Task(models.Model):
	authenticated_user = models.ForeignKey(User, unique=False, null=False, default=None)
	task_name = models.CharField(max_length=300, unique=False, default='None')
	due_date = models.CharField(max_length=255, default='None')
	percent_to_complete = models.IntegerField(default=0)
	estimated_time = models.DecimalField(max_digits=None, decimal_places=None, default=0.0)
	priority = models.IntegerField(default=0)
	pomodoro = models.BooleanField(default=False, unique=False)
	todo = models.CharField(max_length=500, unique=False, default='None')
