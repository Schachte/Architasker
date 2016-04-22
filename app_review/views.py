from __future__ import absolute_import
from __future__ import print_function
import datetime
import httplib2
import argparse
import os
import logging
import collections
import time
import urllib
import pytz
import json
import re
from random import randint
from pytz import timezone
from dateutil.parser import parse
from apiclient import discovery
import math
from decimal import Decimal
from django.template import loader, Context
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.core.cache import cache
from django.utils.cache import get_cache_key
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from dateutil import tz

from app_tasks.models import BreakdownUserTask as BUT
from .models import ReviewModel as Review
import json

from app_account_management.models import UserExtended
from app_calendar.views import convert
from collections import OrderedDict


def reviewal_check(request):


	current_user_extended = UserExtended.objects.get(authenticated_user=request.user)
	current_user_time_zone = current_user_extended.time_zone
	current_user_time_zone = pytz.timezone(str(current_user_time_zone))
	current_time = datetime.datetime.now(current_user_time_zone)

	#Check the last date to review

	current_time = str(current_time)
	current_time = current_time[0:11] + "00:00:00+00:00"
	current_time = parse(current_time)
	data_to_review = BUT.objects.filter(reviewed=0, start_time__lt=current_time).order_by('start_time')
	tasks_to_review = {}

	print(data_to_review[0].start_time)

	for each_item in data_to_review:
		print(each_item.start_time)
		item_date = str(each_item.start_time)
		already_exists = False
		if item_date[0:10] not in tasks_to_review:
			tasks_to_review[item_date[0:10]] = [[convert(each_item.parent_task.task_name), (parse(each_item.end_time)-parse(each_item.start_time)).total_seconds() / 3600]]
		else:
			#Loops through exisiting tasks in key for day
			for task_in_array_already in tasks_to_review[item_date[0:10]]:
				if task_in_array_already[0] == each_item.parent_task.task_name:
					task_in_array_already[1] += (parse(each_item.end_time)-parse(each_item.start_time)).total_seconds() / 3600
					already_exists = True

			if(already_exists == False):
				tasks_to_review[item_date[0:10]].append([convert(each_item.parent_task.task_name), (parse(each_item.end_time)-parse(each_item.start_time)).total_seconds() / 3600])

	tasks_to_review = OrderedDict(sorted(tasks_to_review.items()))
	print(tasks_to_review)
	json_list_return = json.dumps(tasks_to_review, sort_keys=False)

	return HttpResponse(json_list_return)