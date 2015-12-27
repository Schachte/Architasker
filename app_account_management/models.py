from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User
from procrastinate.models import *

# Create your models here.

class UserExtended(models.Model):
	authenticated_user = models.ForeignKey(User, unique=False, null=False, default=None)
	# dob = models.DateField(default=None, null=True)
	time_zone = models.CharField(max_length=255, default='None')
	google_auth = models.BooleanField(default=False, unique=False)
	user_login_count = models.IntegerField(default=0)
