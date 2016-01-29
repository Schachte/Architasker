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
import re
from random import randint

from pytz import timezone
from dateutil.parser import parse
from apiclient import discovery

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

from app_calendar.models import UserEvent as SNE
from app_calendar.models import CredentialsModel
from procrastinate import settings
from app_account_management.models import UserExtended

from operator import itemgetter

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


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to dynamically call the range of dates for the week the user is in
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def get_current_week_range(request):

	#Request the user that is logged in
	current_user = User.objects.get(username=request.user.username)

	#Get a query set for all of the events that the user has under their account
	current_user_ext = UserExtended.objects.get(authenticated_user=current_user)

	#Days left in the current week (to get the date for Sunday)
	now_utc = datetime.datetime.utcnow()
	local_tz = pytz.timezone(current_user_ext.time_zone)
	now_utc = pytz.utc.localize(now_utc)
	local_time = now_utc.astimezone(local_tz)
	delta_for_BOW = 0 + local_time.weekday()
	delta_for_EOW = 6 - local_time.weekday()

	#Get the date for the end of the current week
	current_EOW = local_time + datetime.timedelta(days=delta_for_EOW)
	current_BOW = local_time - datetime.timedelta(days=delta_for_BOW)

	now = current_BOW  #Current place within the week
	then = current_EOW #End of week for the current week

	#Format for UTC Time
	now = now.isoformat() + 'Z'
	then = then.isoformat() + 'Z'

	now = str(now[0:10]) + 'T00:00:01Z'
	then = str(then[0:10]) + 'T23:59:59Z'

	#Build a list of beginning and end of week to return from the function
	time_range = [now, then]

	#Return the start and end times
	return time_range

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to parse out invalid time formats caused by the parse function
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def parse_conversions(initial_date):
	if '+' in initial_date:
		initial_date = initial_date.replace(' ', 'T')
		initial_date = initial_date.replace('+', 'Z')
		initial_date = initial_date[0:20]
		return initial_date
	else:
		return initial_date

#Test function designed to check the open times for each day
def task_distribution(request):

	#Get the current user based on the request variable
	current_user = User.objects.get(username=request.user.username)

	#Get a query set for all of the events that the user has under their account
	current_user_ext = UserExtended.objects.get(authenticated_user=current_user)

	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	#Get a query set for all of the events that the user has under their account
	user_events = SNE.objects.filter(authenticated_user=current_user, start_time__range=[parse(start_week_range), parse(end_week_range) + datetime.timedelta(days=1)])

	#Array that will hold the start and end times for events already programmed
	start_times         = []
	end_times           = []

	#loop through all the events associated with the currently logged in user
	counter = 0
	sorted_event_start_end_times = []

	#Go through all the user events within the week range that was calculated
	for each_event in user_events:

		#Get the string representation for the queried objects
		current_start_time = each_event.start_time
		current_end_time = each_event.end_time

		#If this is not an all day event, then append to the start and end time arrays
		if not 'T00:00:00Z' in current_start_time and not 'T00:00:00Z' in current_end_time:
			start_times.append(current_start_time)
			end_times.append(current_end_time)

	#Loop, sort and append start times 
	for index, st in enumerate(start_times):
		try:
			temp_tuple = (st, end_times[index])
			sorted_event_start_end_times.append(temp_tuple)
		except:
			pass

	#Sort the start and end tuple array
	sorted_event_start_end_times.sort(key=lambda x: x[0])

	#Get the raw string representation of the wakeup and bed times
	wakeup_time = current_user_ext.wakeup_time
	sleepy_time = current_user_ext.sleepy_time

	free_blocks  = []
	week_day_cluster = {}   #Used to hold the clustered time data for the current week

	'''''''''''''''''''''''''''''''''''''''''''''
	Segregating taken blocks into day dictionaries
	'''''''''''''''''''''''''''''''''''''''''''''
	#Initialize the keys in the dict.
	week_day_cluster['0']       = []
	week_day_cluster['1']       = []
	week_day_cluster['2']       = []
	week_day_cluster['3']       = []
	week_day_cluster['4']       = []
	week_day_cluster['5']       = []
	week_day_cluster['6']       = []
	#If the item is a multi day event do we treat the item like it is an all day event?

	#Looping and categorizing events day by data and persisting into dictionaries
	for sorted_data in sorted_event_start_end_times:
		if parse(sorted_data[0].encode("utf-8")).weekday() == 0 and parse(sorted_data[1].encode("utf-8")).weekday() == 0:
			week_day_cluster['0'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])
		elif parse(sorted_data[0].encode("utf-8")).weekday() == 1 and parse(sorted_data[1].encode("utf-8")).weekday() == 1:
			week_day_cluster['1'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])
		elif parse(sorted_data[0].encode("utf-8")).weekday() == 2 and parse(sorted_data[1].encode("utf-8")).weekday() == 2:
			week_day_cluster['2'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])
		elif parse(sorted_data[0].encode("utf-8")).weekday() == 3 and parse(sorted_data[1].encode("utf-8")).weekday() == 3:
			week_day_cluster['3'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])
		elif parse(sorted_data[0].encode("utf-8")).weekday() == 4 and parse(sorted_data[1].encode("utf-8")).weekday() == 4:
			week_day_cluster['4'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])
		elif parse(sorted_data[0].encode("utf-8")).weekday() == 5 and parse(sorted_data[1].encode("utf-8")).weekday() == 5:
			week_day_cluster['5'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])
		elif parse(sorted_data[0].encode("utf-8")).weekday() == 6 and parse(sorted_data[1].encode("utf-8")).weekday() == 6:
			week_day_cluster['6'].append([(sorted_data[0].encode("utf-8"), sorted_data[1].encode("utf-8"))])

	#This is the dictionary of data that is going to hold the free time range tuples for each day in the current week
	all_free_times = {}

	#Initializing empty arrays for the dictionary keys
	all_free_times[0] = []
	all_free_times[1] = []
	all_free_times[2] = []
	all_free_times[3] = []
	all_free_times[4] = []
	all_free_times[5] = []
	all_free_times[6] = []

	#This is the dictionary of data that holds the min start time of each day
	min_day_start_times = {}

	#This is the dictionary of data that holds the min start time of each day
	max_day_start_times = {}

	#Array to keep track of the dates for values in dictionary that are empty
	days_in_current_week = []

	#Loop through the dates in the current week and append them to the list
	for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
		days_in_current_week.append(str(single_date))

	'''''''''''''''''''''''''''''''''''''''''''''''
	FINDING MIN/MAX TIMES THAT OVERLAP WAKEUP TIME
	'''''''''''''''''''''''''''''''''''''''''''''''
	for key, event_start_end in week_day_cluster.iteritems():
		try:
			#Arrays to filter out event min and max times 
			temp_min = []
			temp_max = []

			#Converting the wakeup time to the current day of the week with database wakeup value
			temp_wakeup_time    = wakeup_time
			new_wakeup_time     = days_in_current_week[int(key)][0:11] + temp_wakeup_time + ':00Z'
			new_wakeup_time     = new_wakeup_time.replace(' ', 'T')
			new_wakeup_time     = parse(new_wakeup_time)

			for start_end in event_start_end:

				#Date object conversions on event start and end times
				event_start_object  = parse(start_end[0][0])
				event_end_object    = parse(start_end[0][1])

				if (len(temp_max) > 0 and event_start_object <= temp_max[len(temp_max)-1]):
					temp_min.append(event_start_object)
					temp_max.append(event_end_object)

				#Checking if event times overlap with the wakeup time
				if (event_start_object <=  new_wakeup_time <= event_end_object):
					temp_min.append(event_start_object)
					temp_max.append(event_end_object)

				temp_min.sort()
				temp_max.sort()

			min_day_start_times[int(key)] = (str(temp_min[0]))
			max_day_start_times[int(key)] = (str(temp_max[len(temp_max)-1]))

		except:
			pass

	'''''''''''''''''''''
	DEALING WITH 0 (WAKEUP)
	'''''''''''''''''''''

	temp_wakeup_time = wakeup_time
	sleep_time = current_user_ext.sleepy_time #21:00
	temp_sleep_time = sleep_time

	for key, event_start_end in week_day_cluster.iteritems():

		if len(event_start_end) > 0:
			if int(key) in min_day_start_times and int(key) in max_day_start_times:
				wakeup_time = str(max_day_start_times[int(key)]).replace(' ', 'T')[0:19] + 'Z'

			else:
				wakeup_time = event_start_end[0][0][0][0:11]
				wakeup_time = wakeup_time + temp_wakeup_time + ':00Z'

			for index, event in enumerate(event_start_end):
				if (parse(wakeup_time) < parse(event[0][0])):

					wakeup_time = wakeup_time.encode('utf-8')
					beginning_wakeup_time_comparison = event[0][0][0:11]
					beginning_wakeup_time_comparison += current_user_ext.wakeup_time + ':00Z'

					#print("parse(event[0][0]) is: %s"%(str(parse(event[0][0]))))
					#print("Wakeup time is: %s"%(wakeup_time))
					#print(((parse(event[0][0]) - parse(wakeup_time)).seconds)/60)

					if (((parse(event[0][0]) - parse(wakeup_time)).seconds)/60 >= (current_user_ext.min_task_time)):
						#print("A) Free time for %s is %s to %s"%(key, str(parse(wakeup_time)), event[0][0]))

						wakeup_time = str(parse(wakeup_time))
						sleep_time = event[0][0]
						wakeup_time = parse_conversions(wakeup_time)
						sleep_time = parse_conversions(sleep_time)
						wakeup_time = wakeup_time.encode('utf-8')
						sleep_time = sleep_time.encode('utf-8')
						all_free_times[int(key)].append((wakeup_time, sleep_time))

					break
			else:

				sleep_time = event_start_end[0][0][0][0:11]
				sleep_time = sleep_time + temp_sleep_time + ':00Z'
				#print(wakeup_time)
				#print(sleep_time)

				if (parse(wakeup_time) + datetime.timedelta(minutes=current_user_ext.min_task_time) < parse(sleep_time)):
					#print("C)Free time for %s is %s to %s"%(key, str(parse(wakeup_time))), str(parse(sleep_time)))
					
					wakeup_time = parse_conversions(wakeup_time)
					sleep_time = parse_conversions(sleep_time)
					wakeup_time = wakeup_time.encode('utf-8')
					sleep_time = sleep_time.encode('utf-8')
					all_free_times[int(key)].append((wakeup_time, sleep_time))
		else:

			#print("INDEX FOR THE DAY IS : %s"%(key))

			wakeup_time = str(parse(start_week_range) + datetime.timedelta(days=int(key)))[0:11]

			wakeup_time = wakeup_time + temp_wakeup_time + ':00Z'

			sleep_time = current_user_ext.sleepy_time #21:00

			temp_sleep_time = sleep_time

			sleep_time = wakeup_time[0:11]

			sleep_time = sleep_time + temp_sleep_time + ':00Z'

			wakeup_time = wakeup_time.replace(' ', 'T')

			sleep_time = sleep_time.replace(' ', 'T')

			wakeup_time = wakeup_time.encode('utf-8')
			sleep_time = sleep_time.encode('utf-8')

			all_free_times[int(key)].append((wakeup_time, sleep_time))

			#print("SUCCESS APPENDED FOR %s"%(key))

			#print(all_free_times)

	'''''''''''''''''''''
	DEALING WITH N (EVENTS)
	'''''''''''''''''''''

	for key, event_start_end in week_day_cluster.iteritems():

		#initializing the cluster vals for parallel/conflicting events
		if (len(event_start_end) > 0):
			min_start_time_for_cluster = parse(event_start_end[0][0][0])

			max_end_time_for_cluster = parse(event_start_end[0][0][1])
			is_parallel = False

		for index, start_end in enumerate(event_start_end):

			beginning_wakeup_time_comparison = start_end[0][0][0:11]
			beginning_wakeup_time_comparison += current_user_ext.wakeup_time + ':00Z'

			event_start_time = event_start_end[int(index)][0][0]
			sleep_time = current_user_ext.sleepy_time #21:00
			temp_sleep_time = sleep_time
			sleep_time = event_start_time[0:11]
			sleep_time = sleep_time + temp_sleep_time + ':00Z'
			temp_tuple = (event_start_time, sleep_time)

			#print("The end time for the event is ",)
			#print(event_start_time)

			if (not parse(event_start_time) > parse(sleep_time)):

				if (index > 0):
					#Converting into a date object
					event_end_time = event_start_end[index-1][0][1]

					#Adding the 15 minutes
					event_end_time = parse(event_end_time)

					#Parallel cluster algorithm (credit to fatima)
					if (parse(start_end[0][0]) < max_end_time_for_cluster):
						is_parallel = True
						if (parse(start_end[0][1]) > max_end_time_for_cluster):
							max_end_time_for_cluster = parse(start_end[0][1])
						   
					else:
						if (is_parallel):
							is_parallel = False

						min_start_time_for_cluster = parse(start_end[0][0])
						max_end_time_for_cluster = parse(start_end[0][1])

						if (((parse(start_end[0][0]) - event_end_time).seconds)/60 >= (current_user_ext.min_task_time) and event_end_time >= parse(beginning_wakeup_time_comparison)):
							if parse(start_end[0][0]) >= event_end_time + datetime.timedelta(minutes=current_user_ext.min_task_time):

								#Check if key exists inside of the dictionary
								if (event_end_time, str(start_end[0][0])) not in all_free_times[int(key)]:
									wakeup_time = str(event_end_time)
									wakeup_time = wakeup_time.encode('utf-8')
									sleep_time = start_end[0][0]
									sleep_time = sleep_time.encode('utf-8')

									wakeup_time = parse_conversions(wakeup_time)
									sleep_time = parse_conversions(sleep_time)

									all_free_times[int(key)].append((wakeup_time, sleep_time))


				elif len(event_start_end) == 1 and parse(start_end[0][0]) > parse(beginning_wakeup_time_comparison):
					event_end_time = event_start_end[0][0][1]
					sleep_time = current_user_ext.sleepy_time #21:00
					temp_sleep_time = sleep_time
					sleep_time = event_end_time[0:11]
					sleep_time = sleep_time + temp_sleep_time + ':00Z'
					event_end_time = event_end_time.encode('utf-8')
					sleep_time = sleep_time.encode('utf-8')
					temp_tuple = (event_end_time, sleep_time)
					all_free_times[int(key)].append((temp_tuple))





	'''''''''''''''''''''
	DEALING WITH K (BEDTIME)
	'''''''''''''''''''''
	#Loop through the end times for all the week day clustered data sets
	for key, event_start_end in week_day_cluster.iteritems():
		#List to hold all the end-times before sorting
		end_time_data = []

		#If the association in the dictionary has information, then continue
		if (len(event_start_end) > 0):
			temp_bed_time = event_start_end[0][0][1][0:11] + current_user_ext.sleepy_time + ":00Z" 
			temp_bed_time = parse(temp_bed_time)


			#add each end time
			for each_list_tuple in event_start_end:

				if (parse(each_list_tuple[0][1]) > temp_bed_time and parse(each_list_tuple[0][0]) > temp_bed_time):
					continue
				end_time_data.append(each_list_tuple[0][1])

			#Sort and string format the data
			temp_bed_time = sorted(end_time_data)[len(end_time_data)-1][0:11]
			temp_bed_time += current_user_ext.sleepy_time + ":00Z"

			#Reverse back in the list of end times until you hit the first end time that is less than the users bedtime
			#Converting bed time to date for comparisons
			parsed_temp_bed_time = parse(temp_bed_time)

			#Convert to date time object
			current_day_end_time = parse(sorted(end_time_data)[len(end_time_data)-1])

			##Printing data THAT SHOULD BE CONVERTED TO THE APPENDING DATA
			#print("The temp bed time is %s"%(temp_bed_time))
			#print("The current day time end is %s"%(current_day_end_time))
			if (current_day_end_time + datetime.timedelta(minutes=current_user_ext.min_task_time) <= parse(temp_bed_time)):
				# current_day_end_time += datetime.timedelta(minutes=current_user_ext.travel_time)
				# #print("(%s, %s)"%(str(current_day_end_time), temp_bed_time))
				try:
					current_day_end_time = parse_conversions(str(current_day_end_time))
					current_day_end_time = current_day_end_time.encode('utf-8')
					temp_bed_time = parse_conversions(temp_bed_time)
					temp_bed_time = temp_bed_time.encode('utf-8')
					all_free_times[int(key)].append((str(current_day_end_time), temp_bed_time))
				except:
					#print("WE HAVE HIT THE EXCEP BLOCK!")
					pass
			# else:
			#     current_day_end_time = ''

			#     for task_end_times in reversed(end_time_data):
			#         if (parse(task_end_times) < parsed_temp_bed_time):
			#             #print("reversal data: %s"%(task_end_times))
			#             current_day_end_time = parse(task_end_times)
			#             all_free_times[int(key)].append((str(current_day_end_time), temp_bed_time))
			#             break

		#Entire day is free
		else:
			wakeup_time = days_in_current_week[int(key)][0:10]
			wakeup_time += "T%s:00Z"%(current_user_ext.wakeup_time)
			sleepy_time = days_in_current_week[int(key)][0:10]
			sleepy_time += "T%s:00Z"%(current_user_ext.sleepy_time)

			try:
				wakeup_time = parse_conversions(wakeup_time)
				sleepy_time = parse_conversions(sleepy_time)
				wakeup_time = wakeup_time.encode('utf-8')
				sleepy_time = sleepy_time.encode('utf-8')
				all_free_times[int(key)].append((wakeup_time, sleepy_time))
			except:
				pass

	final_free_time_tuples = []
	for each_list in all_free_times.iteritems():
		for each_tuple in each_list[1]:
			if (not each_tuple in final_free_time_tuples):
				final_free_time_tuples.append(each_tuple)

	print('''

 ___ ___ ___ ___ _  _   ___ ___ ___ ___   ___ _    ___   ___ _  _____ 
| _ ) __/ __|_ _| \| | | __| _ \ __| __| | _ ) |  / _ \ / __| |/ / __|
| _ \ _| (_ || || .` | | _||   / _|| _|  | _ \ |_| (_) | (__| ' <\__ |
|___/___\___|___|_|\_| |_| |_|_\___|___| |___/____\___/ \___|_|\_\___/
                                                                      
		''')
	for data in final_free_time_tuples:
		print(data)

	print('''
 ___ _  _ ___    ___ ___ ___ ___   ___ _    ___   ___ _  _____ 
| __| \| |   \  | __| _ \ __| __| | _ ) |  / _ \ / __| |/ / __|
| _|| .` | |) | | _||   / _|| _|  | _ \ |_| (_) | (__| ' <\__ |
|___|_|\_|___/  |_| |_|_\___|___| |___/____\___/ \___|_|\_\___/                                                           
	''')


	return HttpResponse("The user has been queried successfully!")

