from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User

class UserTask(models.Model):
	authenticated_user = models.ForeignKey(User, unique=False, null=False, default=None)
	task_name = models.CharField(max_length=300, unique=False, default='None')
	due_date = models.CharField(max_length=255, default='None')
	day_date = models.CharField(max_length=255, default='None')
	day_num = models.IntegerField(default=0)
	percent_to_complete = models.IntegerField(default=0)
	estimated_time = models.DecimalField(max_digits=6, decimal_places=3, default=0.0)
	difficulty = models.IntegerField(default=0)
	continuous = models.BooleanField(default=False, unique=False)
	pomodoro = models.BooleanField(default=False, unique=False)
	todo = models.CharField(max_length=500, unique=False, default='None')
	color = models.CharField(max_length=255, default='None')
	url = models.CharField(max_length=255, default='None')
	location = models.CharField(max_length=255, default='None')
	comments = models.CharField(max_length=800, default='None')
	priority = models.IntegerField(default=0)
	percentile = models.IntegerField(default=0)



#create to do model, ajax call to store everything. w/ char field and foreign key (pk) ... crossed off, deleted, etc states need to be stored
#event colors
#reminder link for settings
#location
#url
#Extra/Description/Comments
#continuous/consecutive event
#to do list