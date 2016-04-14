from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User

TRANSIT_CHOICES = (
    (1, 'driving'),
    (2, 'biking'),
    (3, 'walking'),
)


DAY_CHOICES = (
    (0, 'monday'),
    (1, 'tuesday'),
    (2, 'wednesday'),
    (3, 'thursday'),
    (4, 'friday'),
    (5, 'saturday'),
    (6, 'sunday')
)

class UserTask(models.Model):
	authenticated_user = models.ForeignKey(User, unique=False, null=False, default=None)
	task_name = models.CharField(max_length=300, unique=False, default='None')
	due_date = models.CharField(max_length=255, default='None')
	day_date = models.CharField(max_length=255, default='None')
	day_num = models.IntegerField(default=0)
	percent_to_complete = models.FloatField(blank=True, null=True, default=0)
	estimated_time = models.FloatField(blank=True, null=True, default=0)
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
	transit_mode = models.IntegerField(choices=TRANSIT_CHOICES, default=1)
	percent_distributed = models.FloatField(blank=True, null=True, default=0)
	mon_task_time = models.FloatField(blank=True, null=True, default=0)
	tues_task_time = models.FloatField(blank=True, null=True, default=0)
	wed_task_time = models.FloatField(blank=True, null=True, default=0)
	thurs_task_time = models.FloatField(blank=True, null=True, default=0)
	fri_task_time = models.FloatField(blank=True, null=True, default=0)
	sat_task_time = models.FloatField(blank=True, null=True, default=0)
	sun_task_time = models.FloatField(blank=True, null=True, default=0)

	def __str__(self):
		return self.task_name


class BreakdownUserTask(models.Model):
	parent_task = models.ForeignKey(UserTask, unique=False, null=False, default=None)
	# sub_task = models.ForeignKey(UserTask, unique=False, null=False, default=None)
	start_time = models.CharField(max_length=255, default='None')
	end_time = models.CharField(max_length=255, default='None')
	current_day = models.IntegerField(choices=DAY_CHOICES, default=0)
	# task_name = models.ForeignKey(UserTask.task_name, unique=False, null=False, default=None)

	def __str__(self):
		return self.parent_task.task_name





#create to do model, ajax call to store everything. w/ char field and foreign key (pk) ... crossed off, deleted, etc states need to be stored
#event colors
#reminder link for settings
#location
#url
#Extra/Description/Comments
#continuous/consecutive event
#to do list