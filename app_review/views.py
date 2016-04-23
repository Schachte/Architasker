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

from collections import OrderedDict



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to convert unicode dictionaries into str dictionaries
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def convert(data):
    if isinstance(data, basestring):
        return data.encode('utf-8')
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data



def reviewal_dictionary(request):

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

	return tasks_to_review

def reviewal_check(request):

	tasks_to_review = reviewal_dictionary(request)
	
	print(tasks_to_review)
	json_list_return = json.dumps(tasks_to_review, sort_keys=False)

	return HttpResponse(json_list_return)


def submit_reviewal(request):

	if request.method == 'POST':
		print("asuh")
		x = request.POST.get('task_reviewal')
		current_user = User.objects.get(id=request.user.id)

		d = json.loads(x)
		

		for each_key in d:

			if (each_key['task_hours_complete'] == ""):
				each_key['task_hours_complete'] = -1
			try:
				if (not each_key['task_hours_complete'] == -1):
					temp_model = Review.objects.create(
						authenticated_user = current_user,
						task_name = each_key['task_name'],
						date_assigned = each_key['task_date'],
						hours_completed = float(each_key['task_hours_complete']),
						hours_assigned = float(each_key['task_hours']),
					)	
					temp_model.save()
					print("model saved successfully!")

					current_date_beg = temp_model.date_assigned + " 00:00:00"
					current_date_end = temp_model.date_assigned + " 23:59:00"

					data_to_mark_reviewed = BUT.objects.filter(parent_task__authenticated_user=request.user, parent_task__task_name=temp_model.task_name, start_time__range=[parse(current_date_beg), parse(current_date_end)])
					print("ppppppppp")
					if (not each_key['task_hours_complete'] == -1):
						print("SETTING TO 1")
						for each_mini_task in data_to_mark_reviewed:
							each_mini_task.reviewed = 1
							each_mini_task.save()

			except Exception as e:
				print(e)




	return HttpResponse('None')


def data_for_charts(request):

	#Variable that stores the current time based on the timezone of the user account
	current_user_extended = UserExtended.objects.get(authenticated_user=request.user)
	current_user_time_zone = current_user_extended.time_zone
	current_user_time_zone = pytz.timezone(str(current_user_time_zone))
	current_time = datetime.datetime.now(current_user_time_zone)
	current_date = str(current_time)[0:10]
	current_time = str(current_time)
	# current_time = current_time[0:19] + "Z"
	# current_time = parse(current_time)

	current_date_beg = current_time + " 00:00:00"

	past_seven_days = Review.objects.filter(authenticated_user=request.user, date_assigned__range=[parse(current_date_beg) - datetime.timedelta(days=8), parse(current_date_beg)], hours_completed__gt=0.0)
	
	print(past_seven_days)
	print(parse(current_date_beg) - datetime.timedelta(days=7))
	print(parse(current_date_beg))

	data_points_dictionary = {}
	data_points_dictionary_final = {}

	for each_review in past_seven_days:
		if each_review.date_assigned not in data_points_dictionary:
			data_points_dictionary[each_review.date_assigned] = [each_review.hours_completed/each_review.hours_assigned]
		else:
			data_points_dictionary[each_review.date_assigned].append(each_review.hours_completed/each_review.hours_assigned)

	for key, value in data_points_dictionary.iteritems():
		data_points_dictionary_final[key] = sum(value)/len(value)
		print("Key: %s Efficiency: %.2f"%(key, sum(value)/len(value)))




