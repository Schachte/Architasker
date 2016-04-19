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

from app_calendar.models import UserEvent as SNE
from app_calendar.models import CredentialsModel
from procrastinate import settings
from app_account_management.models import UserExtended
from app_tasks.models import UserTask as Task
from operator import itemgetter
from app_tasks.models import BreakdownUserTask 
from operator import itemgetter
import urllib, json

from random import choice
from string import ascii_uppercase
from app_tasks.models import BreakdownUserTask as BUT
from django.core import serializers

from collections import namedtuple



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Rounding numbers to the nearest .5 value
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def round_numbers(task_hours):
	return (round(task_hours*12)/12)


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

def format_addresses(address_input):
	new_address = ''
	list_convert = address_input.split(' ')
	new_address += list_convert[0]
	for each_element in list_convert[1:]:
		new_address+='+' + each_element
	new_address = new_address.strip()
	return new_address

def get_transit_mode(task_obj):
	return task_obj.transit_mode

def get_transit_type(type_int):
	if (type_int == '1'):
		return 'walking'
	elif (type_int == '2'):
		return 'biking'
	elif (type_int == '3'):
		return 'driving'
	else:
		return 'Error'

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Build a geolocation function to get the lat and long from addresses
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def geoencoder(request, task1_object, task2_object, primary_mode_of_travel):

	a_1 = format_addresses(task1_object.location)
	a_2 = format_addresses(task2_object.location)

	location_1_lat = ''
	location_1_long = ''

	location_2_lat = ''
	location_2_long = ''

	url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=AIzaSyBuEDTHE8gFHtbIOf4tcNfQGZxRlyqqKY8"%(a_1)
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	data = convert(data)
	print('Location 1 coordinates: ')
	print(str(data['results'][0]['geometry']['location']['lat']) + ', ' + str(data['results'][0]['geometry']['location']['lng']))

	location_1_lat 	= str(data['results'][0]['geometry']['location']['lat'])
	location_1_long = str(data['results'][0]['geometry']['location']['lng'])

	url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=AIzaSyBuEDTHE8gFHtbIOf4tcNfQGZxRlyqqKY8"%(a_2)
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	data = convert(data)
	print(str(data['results'][0]['geometry']['location']['lat']) + ', ' + str(data['results'][0]['geometry']['location']['lng']))

	location_2_lat 	= str(data['results'][0]['geometry']['location']['lat'])
	location_2_long = str(data['results'][0]['geometry']['location']['lng'])

	travel_time_url = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins=%s,%s&destinations=%s,%s&mode=%s&key=AIzaSyCdyoZAV_lsXz8nV54SKIGgtZ45Auhwnss'%(location_1_lat, location_1_long, location_2_lat, location_2_long, primary_mode_of_travel)
	response = urllib.urlopen(travel_time_url)
	data = json.loads(response.read())
	data = convert(data)
	print(data['rows'][0]['elements'][0]['duration']['text'])

	return data['rows'][0]['elements'][0]['duration']['text']

def get_primary_mode_of_travel(t1, t2):
	print(t1.transit_mode)
	print('^ is transit mode')
	if (t1.transit_mode == 1 or t2.transit_mode == 1):
		return 'driving'
	elif (t1.transit_mode == 2 or t2.transit_mode == 2):
		return 'bicycling'
	else:
		return 'walking'

def get_travel_time(request):
	current_user = User.objects.filter(username=request.user.username)
	all_user_tasks = UserTask.objects.all()

	a_1 = all_user_tasks[0]
	a_2 = all_user_tasks[1]

	primary_transit = get_primary_mode_of_travel(a_1, a_2)
	print("primary transit is %s"%(primary_transit))

	total_time = geoencoder(request, a_1, a_2, primary_transit)
	
	return HttpResponse('<b><center><h2>It will take %s minutes to get from %s to %s by mode of %s</h2></center></b>'%(total_time, a_1.location, a_2.location, primary_transit))


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

	#Take all the data in this list and convert it to a tuple
	mon 	= []
	tues 	= []
	wed 	= []
	thurs 	= []
	fri 	= []
	sat 	= []
	sun 	= []

	for data in final_free_time_tuples:
		print(parse(data[0]).weekday())
		if (parse(data[0]).weekday() == 0):
			mon.append(data)
		elif (parse(data[0]).weekday() == 1):
			tues.append(data)
		elif (parse(data[0]).weekday() == 2):
			wed.append(data)
		elif (parse(data[0]).weekday() == 3):
			thurs.append(data)
		elif (parse(data[0]).weekday() == 4):
			fri.append(data)
		elif (parse(data[0]).weekday() == 5):
			sat.append(data)
		elif (parse(data[0]).weekday() == 6):
			sun.append(data)

	dictionary_free_blocks = {'0': mon, '1': tues, '2': wed, '3': thurs, '4': fri, '5':sat, '6': sun}

	print('''
 ___ _  _ ___    ___ ___ ___ ___   ___ _    ___   ___ _  _____ 
| __| \| |   \  | __| _ \ __| __| | _ ) |  / _ \ / __| |/ / __|
| _|| .` | |) | | _||   / _|| _|  | _ \ |_| (_) | (__| ' <\__ |
|___|_|\_|___/  |_| |_|_\___|___| |___/____\___/ \___|_|\_\___/                                                           
	''')

	#shouldn't the tuples be returned
	#return dictionary instead of list
	# return HttpResponse("The user has been queried successfully!")
	return dictionary_free_blocks



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
 
    return time_range


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Calculate overall priority and percentile for each task
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def prioritize_and_cluster(request):

	current_user = User.objects.get(username=request.user.username)

	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[datetime.datetime.now(), parse(end_week_range) + datetime.timedelta(days=1)])

	for task in user_tasks:
		print(task.task_name)

	'''
	Calculate and Store Priority
	'''

	for task in user_tasks:
		priority = task.estimated_time / (task.day_num - datetime.datetime.today().weekday()) + task.difficulty
		print(task.task_name + " Priority: " + str(priority))
		#Check output of current day tomorrow
		#print("Current Day: " + str(datetime.datetime.today().weekday()))
		task.priority = priority
		task.save()

	'''
	Calculate and Store Percentile
	'''

	equation_N = user_tasks.count()

	for task in user_tasks:

		equation_L = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(start_week_range), parse(end_week_range) + datetime.timedelta(days=1)], priority__lt=task.priority).count()
		equation_S = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(start_week_range), parse(end_week_range) + datetime.timedelta(days=1)], priority=task.priority).count()
		
		pr_percent = ((equation_L + (0.5*equation_S)) / equation_N)*100
		print(task.task_name + " Percentile: " + str(pr_percent))

		task.percentile = pr_percent
		task.save()

	return HttpResponse("Priority and clusters have been calculated successfully!")


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Calculate number of free hours available per day
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def free_hours_per_day(request):

	#what is this even doing?! ... it's not returning anything, right?! ... fix with Ryan
	# free_time_blocks = task_distribution(request)
	# for data in free_time_blocks:
	# 	print(data)

		#what if key is empty and there is no free time for day....take that into consideration
	# free_time_blocks = {
 #    	0: [('2016-01-25T07:00:00Z', '2016-01-25T14:00:00Z'), ('2016-01-25T15:00:00Z', '2016-01-25T17:05:00Z'), ('2016-01-25T19:50:00Z', '2016-01-25T23:00:00Z')],
 #    	1: [('2016-01-26T07:00:00Z', '2016-01-26T15:10:00Z'), ('2016-01-26T16:55:00Z', '2016-01-26T21:05:00Z')],
 #    	2: [('2016-01-27T07:00:00Z', '2016-01-27T14:00:00Z'), ('2016-01-27T15:00:00Z', '2016-01-27T17:00:00Z'), ('2016-01-27T19:40:00Z', '2016-01-27T23:00:00Z')],
 #    	3: [('2016-01-28T07:00:00Z', '2016-01-28T18:55:00Z'), ('2016-01-28T21:20:00Z', '2016-01-28T23:00:00Z')],
 #    	4: [('2016-01-29T07:00:00Z', '2016-01-29T14:00:00Z'), ('2016-01-29T15:00:00Z', '2016-01-29T16:10:00Z'), ('2016-01-29T17:55:00Z', '2016-01-29T23:00:00Z')],
 #    	5: [('2016-01-30T07:00:00Z', '2016-01-30T18:00:00Z'), ('2016-01-30T19:00:00Z', '2016-01-30T23:00:00Z')],
 #    	6: [('2016-01-31T07:00:00Z', '2016-01-31T18:00:00Z'), ('2016-01-31T19:00:00Z', '2016-01-31T23:00:00Z')],
	# }

	
	current_user = User.objects.get(username=request.user.username) #what is request...would this not work without the request?!

	#Variable that stores the current time based on the timezone of the user account
	current_user_extended = UserExtended.objects.get(authenticated_user=request.user)
	current_user_time_zone = current_user_extended.time_zone
	current_user_time_zone = pytz.timezone(str(current_user_time_zone))
	current_time = datetime.datetime.now(current_user_time_zone)
	current_date = str(current_time)[0:10]


	free_time_blocks = task_distribution(request)

	starting_weekday = parse(current_date).weekday()
	print("Starting weekday: " + str(starting_weekday))

	free_hours = []

	for key, value in free_time_blocks.iteritems():
		hours = 0.0
		if(int(key) < starting_weekday):
			print("Before: %s" %key)
			free_hours.insert(int(key), 0)

		elif(int(key) == starting_weekday):
			print("Equal: %s" %key)
			print(current_time)
			for each_tuple in value:
				print(each_tuple)
				if(parse(each_tuple[0]) > current_time):
					print("Here")
					hours += (parse(each_tuple[1]) - parse(each_tuple[0])).total_seconds() / 60
			free_hours.insert(int(key), hours/60)

		else:
			print("After: %s" %key)
			for each_tuple in value:
				#should we be calculating everything in minutes or hours?!?! ... currently in hours
				hours += (parse(each_tuple[1]) - parse(each_tuple[0])).total_seconds() / 60
			free_hours.insert(int(key), hours/60)

	print("Free hours:")
	for index, value in enumerate(free_hours):
		print(str(index) + " " + str(value))

	return free_hours
	# return HttpResponse("Calculated free hours per day successfully!") ...put "request" back as parameter when testing

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Calculate number of tasks hours allocated per day
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def task_hours_per_day(request):

	free_hours_list = free_hours_per_day(request)

	current_user = User.objects.get(username=request.user.username) #what is request...would this not work without the request?!

	#Variable that stores the current time based on the timezone of the user account
	current_user_extended = UserExtended.objects.get(authenticated_user=request.user)
	current_user_time_zone = current_user_extended.time_zone
	current_user_time_zone = pytz.timezone(str(current_user_time_zone))
	current_time = datetime.datetime.now(current_user_time_zone)
	current_date = str(current_time)[0:10]

	print("current user time zone is"),
	print(current_time)

	print("the current day is")
	print(parse(current_date))


	total_free_hours = sum(free_hours_list)
	print("Total free hours: " + str(total_free_hours))


	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)])
	print("User Tasks: " + str(Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)]).count()))

	total_task_hours = 0.0
	for task in user_tasks:
		print(task.task_name)
		#do we want to divide by a 100 here to store it in the database as a decimal
		#Should I change estimated time in database to float
		print("Percent "+ str(task.percent_to_complete))
		print("Task time " +str(task.estimated_time))
		print(task.percent_to_complete * task.estimated_time * (1 - task.percent_distributed))
		total_task_hours += task.percent_to_complete * task.estimated_time * (1 - task.percent_distributed)

		print(total_task_hours)

	print(total_task_hours)

	#Throw error if this is over 1 in user task modal window
	task_time_day_ratio = total_task_hours/total_free_hours

	task_hours_list = []

	for day, free_hours in enumerate(free_hours_list):
		task_hours_list.insert(day, free_hours * task_time_day_ratio)
		print(str(day) + " " + str(task_hours_list[day]))


	for task in user_tasks:
		task_hour_ratio = ( task.percent_to_complete * task.estimated_time * (1 - task.percent_distributed) ) / total_task_hours
		task.mon_task_time = task_hour_ratio * task_hours_list[0]
		task.tues_task_time = task_hour_ratio * task_hours_list[1]
		task.wed_task_time = task_hour_ratio * task_hours_list[2]
		task.thurs_task_time = task_hour_ratio * task_hours_list[3]
		task.fri_task_time = task_hour_ratio * task_hours_list[4]
		task.sat_task_time = task_hour_ratio * task_hours_list[5]
		task.sun_task_time = task_hour_ratio * task_hours_list[6]

		task.save()

		print("Intial times")
		print(task.task_name)
		print(task.mon_task_time)
		print(task.tues_task_time)
		print(task.wed_task_time)
		print(task.thurs_task_time)
		print(task.fri_task_time)
		print(task.sat_task_time)
		print(task.sun_task_time)


	#Need to account for no break tasks at some point

	#should this be separate method?!?!
	'''
	Modified task hours per day
	'''

	task_hours_list_final = task_hours_list

	#need to run for values where day num is smaller than 6 and for when DUE DATE and DAY DATE are equal...MAKE SURE YOU DO THE SECOND PART!!!!
	for early_task in Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], day_num__lt=6):
		#should extimated time * % to complete be stored in the database instead of computing it every time?!
		
		# free_hours_after_task_due = 0.0
		# for index, value in enumerate(free_hours_list):
		# 	if (index > early_task.day_num):
		# 		free_hours_after_task_due += value


		task_time_dictionary = {0: early_task.mon_task_time, 1: early_task.tues_task_time, 2: early_task.wed_task_time, 3: early_task.thurs_task_time, 4: early_task.fri_task_time, 5: early_task.sat_task_time, 6: early_task.sun_task_time}

		print("Hours:" + str(early_task.percent_to_complete * early_task.estimated_time))
		print("Total free time: " + str(total_free_hours))
		print("Hours of free time after day it's due: " + str(sum(free_hours_list[early_task.day_num:])))

		#1) (Task_time)/(Total free time in week) * Hours of free time after day it's due
		hours_allocated_after_due = early_task.percent_to_complete * early_task.estimated_time / total_free_hours * sum(free_hours_list[early_task.day_num:])
		print("Step 1: " + str(hours_allocated_after_due))

		#2) For each day before day due: task time for day + task time for day(#1/total hours of free time before day due)
		for index, value in enumerate(free_hours_list):
			if (index < early_task.day_num): # if we want the assignment to be completed a day before it's due then we can remove the = sign?!
				print("Step 2: " + str(index) + " " + str(sum(free_hours_list[:early_task.day_num])) + " " + str(value))
				
				value_to_change = (value * (hours_allocated_after_due/sum(free_hours_list[:early_task.day_num])))
				task_hours_list_final[index] += value_to_change

				if(index == 0):
					early_task.mon_task_time += value_to_change
				elif(index == 1):
					early_task.tues_task_time += value_to_change
				elif(index == 2):
					early_task.wed_task_time += value_to_change
				elif(index == 3):
					early_task.thurs_task_time += value_to_change
				elif(index == 4):
					early_task.fri_task_time += value_to_change
				elif(index == 5):
					early_task.sat_task_time += value_to_change
				elif(index == 6):
					early_task.sun_task_time += value_to_change

				#task_time_dictionary[index] +=  (value * (hours_allocated_after_due/sum(free_hours_list[:early_task.day_num])))
				early_task.save()

			#3) For each day after day due: task time for day - task time for day(#1/total hours of free time after day due)
			if (index >= early_task.day_num): 
				print("Step 3: " + str(index) + " " + str(sum(free_hours_list[early_task.day_num:])) + " " + str(value))
				
				value_to_change = (value * (hours_allocated_after_due/sum(free_hours_list[early_task.day_num:])))
				task_hours_list_final[index] -= value_to_change

				if(index == 0):
					early_task.mon_task_time -= value_to_change
				elif(index == 1):
					early_task.tues_task_time -= value_to_change
				elif(index == 2):
					early_task.wed_task_time -= value_to_change
				elif(index == 3):
					early_task.thurs_task_time -= value_to_change
				elif(index == 4):
					early_task.fri_task_time -= value_to_change
				elif(index == 5):
					early_task.sat_task_time -= value_to_change
				elif(index == 6):
					early_task.sun_task_time -= value_to_change

				#task_time_dictionary[index] -=  (value * (hours_allocated_after_due/sum(free_hours_list[:early_task.day_num])))
				early_task.save()

		print("Modified times")
		print(early_task.task_name)
		print(early_task.mon_task_time)
		print(early_task.tues_task_time)
		print(early_task.wed_task_time)
		print(early_task.thurs_task_time)
		print(early_task.fri_task_time)
		print(early_task.sat_task_time)
		print(early_task.sun_task_time)


	user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)])
	for task in user_tasks:
		task.mon_task_time = round_numbers(task.mon_task_time)
		task.tues_task_time = round_numbers(task.tues_task_time)
		task.wed_task_time = round_numbers(task.wed_task_time)
		task.thurs_task_time = round_numbers(task.thurs_task_time)
		task.fri_task_time = round_numbers(task.fri_task_time)
		task.sat_task_time = round_numbers(task.sat_task_time)
		task.sun_task_time = round_numbers(task.sun_task_time)

		task.save()

		print("Final times")
		print(task.task_name)
		print(task.mon_task_time)
		print(task.tues_task_time)
		print(task.wed_task_time)
		print(task.thurs_task_time)
		print(task.fri_task_time)
		print(task.sat_task_time)
		print(task.sun_task_time)

	
	#NEED TO CONSIDER IF TASK IS ADDED THE DAY IT IS DUE!!!!!!! Because then sum of free time will be affected...idk

	print("Final work times for week")
	for index, value in enumerate(task_hours_list_final):
		print(str(index) + " " + str(value))

	return task_hours_list_final

	#return HttpResponse("Calculated task hours per day successfully!")


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Array of tasks with lower than 80% completed/distributed 
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def check_80_percent_distribution(high_mid_low):
	lower_than_80 = []
	for task in high_mid_low:
		if(task.percent_distributed < 80):
			lower_than_80.append(task)

	return lower_than_80


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Available task options
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def available_tasks(request):

	#Get the currently logged in user
	current_user = User.objects.get(username=request.user.username)

	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	#Generate cluster segregation
	low = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(start_week_range), parse(end_week_range) + datetime.timedelta(days=1)], percentile__lt=25, percent_distributed__lt=100)
	mid = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(start_week_range), parse(end_week_range) + datetime.timedelta(days=1)], percentile__lt=75, percentile__gt=24, percent_distributed__lt=100)
	high = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(start_week_range), parse(end_week_range) + datetime.timedelta(days=1)], percentile__gt=74, percent_distributed__lt=100)

	avail_tasks = []

	if(len(check_80_percent_distribution(high)) == 0):
		if(len(check_80_percent_distribution(mid)) == 0):
			avail_tasks = list(low) + list(mid) + list(high)

		else:
			avail_tasks = list(high) + check_80_percent_distribution(mid)

	else:
		avail_tasks = check_80_percent_distribution(high)

	return avail_tasks




'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Keep tasks before time new task is added and reset the ones that are 
after the day added
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def task_reset(request):
 
 	#Get the currently logged in user
	current_user = User.objects.get(username=request.user.username)

	#Variable that stores the current time based on the timezone of the user account
	current_user_extended = UserExtended.objects.get(authenticated_user=request.user)
	current_user_time_zone = current_user_extended.time_zone
	current_user_time_zone = pytz.timezone(str(current_user_time_zone))
	current_time = datetime.datetime.now(current_user_time_zone)
	current_date = str(current_time)[0:10]

	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	#get mini tasks after current time
	mini_tasks_after_current_time = BreakdownUserTask.objects.filter(parent_task__authenticated_user=request.user, start_time__range=[current_time, parse(end_week_range) + datetime.timedelta(days=1)])

	for mini_task in mini_tasks_after_current_time:

		day_of_task = parse(mini_task.start_time).weekday()
		task_duration = (parse(mini_task.start_time) - parse(mini_task.end_time)).total_seconds() / 3600

		add_hours_for_task_reset(mini_task.parent_task, day_of_task, task_duration)

		#delete mini task
		print("deleting %s"%(mini_task.parent_task))
		mini_task.delete()



def add_hours_for_task_reset(current_task, current_day_of_week, num_to_add):
	if (current_day_of_week == 0):
		#monday stuff
		current_task.mon_task_time += num_to_add 

	elif (current_day_of_week == 1):
		#tuesday stuff
		current_task.tues_task_time += num_to_add

	elif (current_day_of_week == 2):
		#wedmesdau stuff
		current_task.wed_task_time += num_to_add

	elif (current_day_of_week == 3):
		#tjirs stuf
		current_task.thurs_task_time += num_to_add

	elif (current_day_of_week == 4):
		#frod stuff
		current_task.fri_task_time += num_to_add

	elif (current_day_of_week == 5):
		#saturday stuff
		current_task.sat_task_time += num_to_add

	elif (current_day_of_week == 6):
		#sunday stuff
		current_task.sun_task_time += num_to_add

	current_task.save()


#Get query set/list of all tasks that NEED to be distributed within the current day
def get_tasks_for_day(current_day_of_week, request, current_date):


	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	#Get the currently logged in user
	current_user = User.objects.get(username=request.user.username)

	if (current_day_of_week == 0):
		#monday stuff
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], mon_task_time__gt=0.01)

	elif (current_day_of_week == 1):
		#tuesday stuff
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], tues_task_time__gt=0.01)

	elif (current_day_of_week == 2):
		#wedmesdau stuff
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], wed_task_time__gt=0.01)

	elif (current_day_of_week == 3):
		#tjirs stuf
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], thurs_task_time__gt=0.01)

	elif (current_day_of_week == 4):
		#frod stuff
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], fri_task_time__gt=0.01)

	elif (current_day_of_week == 5):
		#saturday stuff
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], sat_task_time__gt=0.01)

	elif (current_day_of_week == 6):
		#sunday stuff
		user_tasks = Task.objects.filter(authenticated_user=current_user, day_date__range=[parse(current_date), parse(end_week_range) + datetime.timedelta(days=1)], sun_task_time__gt=0.01)

	return user_tasks



def get_task_time_for_day(current_task, current_day_of_week):
	if (current_day_of_week == 0):
		#monday stuff
		user_time = current_task.mon_task_time

	elif (current_day_of_week == 1):
		#tuesday stuff
		user_time = current_task.tues_task_time

	elif (current_day_of_week == 2):
		#wedmesdau stuff
		user_time = current_task.wed_task_time

	elif (current_day_of_week == 3):
		#tjirs stuf
		user_time = current_task.thurs_task_time

	elif (current_day_of_week == 4):
		#frod stuff
		user_time = current_task.fri_task_time

	elif (current_day_of_week == 5):
		#saturday stuff
		user_time = current_task.sat_task_time

	elif (current_day_of_week == 6):
		#sunday stuff
		user_time = current_task.sun_task_time
	return user_time


def subtract_task_time_for_day(current_task, current_day_of_week, num_to_subtract):
	if (current_day_of_week == 0):
		#monday stuff
		current_task.mon_task_time -= num_to_subtract 

	elif (current_day_of_week == 1):
		#tuesday stuff
		current_task.tues_task_time -= num_to_subtract

	elif (current_day_of_week == 2):
		#wedmesdau stuff
		current_task.wed_task_time -= num_to_subtract

	elif (current_day_of_week == 3):
		#tjirs stuf
		current_task.thurs_task_time -= num_to_subtract

	elif (current_day_of_week == 4):
		#frod stuff
		current_task.fri_task_time -= num_to_subtract

	elif (current_day_of_week == 5):
		#saturday stuff
		current_task.sat_task_time -= num_to_subtract

	elif (current_day_of_week == 6):
		#sunday stuff
		current_task.sun_task_time -= num_to_subtract

	current_task.save()


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Allocate tasks
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def allocate_tasks(request):

	print("THE CURRENT USER IS "),
	print(request.user)

	#Get the currently logged in user
	current_user = User.objects.get(username=request.user.username)

	#Get the initial and end date for the current week that we are in
	start_week_range = get_current_week_range(request)[0]
	end_week_range = get_current_week_range(request)[1]

	#Keep tasks before time new task is added and clear/reset the ones that are after the day added
	task_reset(request)

	#Call this function to assign priorities
	prioritize_and_cluster(request)
	
	#Get times of free blocks
	free_blocks = task_distribution(request)

	#Get number of hours that can be spent on tasks per day (array)
	task_hours = task_hours_per_day(request)

	#Variable that stores the current time based on the timezone of the user account
	current_user_extended = UserExtended.objects.get(authenticated_user=request.user)
	current_user_time_zone = current_user_extended.time_zone
	current_user_time_zone = pytz.timezone(str(current_user_time_zone))
	current_time = datetime.datetime.now(current_user_time_zone)
	current_date = str(current_time)[0:10]


	#Looping through the current day of the week to the end of the week
	for int_day_of_week in range(parse(current_date).weekday(), 7):

		#Loop block by block within the current day we're on
		for free_time in free_blocks[str(int_day_of_week)]:

			start_time = free_time[0]
			print(start_time)
			end_time = free_time[1]
			print(end_time)

			available_hours_in_block = (parse(end_time) - parse(start_time)).total_seconds() / 3600

			print("available_hours_in_block is %.8f"%(available_hours_in_block))

			while (available_hours_in_block > 0.0001):

				#Query tasks for the day of the week that need to be distributed
				user_tasks = get_tasks_for_day(int_day_of_week, request, current_date)
				user_tasks = list(user_tasks)

				print("length of user task ssi %d"%(len(user_tasks)))

				if (len(user_tasks) > 0):
				#Grab a random task from the query set
					random_task_index = randint(0, len(user_tasks) - 1)
					random_task = user_tasks[random_task_index]

					print(random_task)
					print("Next free block in the queue is:")
					print(free_time)

					if(get_task_time_for_day(random_task, int_day_of_week) <= available_hours_in_block):
						print("IF STATEMENT START: ")
						print("available hours in block is %.8f"%(available_hours_in_block))
						print("task time for day is %.8f"%(get_task_time_for_day(random_task, int_day_of_week)))
						print("start time is %s"%(start_time))

						random_event_id = ''.join(choice(ascii_uppercase) for i in range(20))
						random_event_id = 'task_' + random_event_id

						mini_task_name = random_task.task_name

						temp_mini_task = BreakdownUserTask.objects.create(
							parent_task = random_task,
							start_time = parse(start_time),
							end_time = parse(start_time) + datetime.timedelta(hours = float(get_task_time_for_day(random_task, int_day_of_week))),
							current_day = parse(start_time).weekday(),
							UID = random_event_id,
							bdt_name = mini_task_name
						)

						temp_mini_task.save()

						print("end time is %s"%(temp_mini_task.end_time))
						print("task duration %.8f"%((temp_mini_task.end_time - temp_mini_task.start_time).total_seconds() / 3600))

						start_time = str(temp_mini_task.end_time + datetime.timedelta(minutes = 15))

						available_hours_in_block -= (((temp_mini_task.end_time - temp_mini_task.start_time).total_seconds() / 3600))
						available_hours_in_block -= .25
						print("available hours in block is %.8f"%(available_hours_in_block))
						subtract_task_time_for_day(temp_mini_task.parent_task, int_day_of_week, (temp_mini_task.end_time - temp_mini_task.start_time).total_seconds() / 3600)

						# if(start_time > end_time):
						# 	available_hours_in_block = 0

					else:

						random_event_id = ''.join(choice(ascii_uppercase) for i in range(20))
						random_event_id = 'task_' + random_event_id

						mini_task_name = random_task.task_name

						temp_mini_task = BreakdownUserTask.objects.create(
							parent_task = random_task,
							start_time = parse(start_time),
							end_time = parse(start_time) + datetime.timedelta(hours = float(available_hours_in_block)),
							current_day = parse(start_time).weekday(),
							UID = random_event_id,
							bdt_name = mini_task_name
						)

						temp_mini_task.save()
						available_hours_in_block = 0
						subtract_task_time_for_day(temp_mini_task.parent_task, int_day_of_week, (temp_mini_task.end_time - temp_mini_task.start_time).total_seconds() / 3600)

				else:
					break


	#Insert a query set to get all mini tasks, find times that are the same, and remove one of them.

	all_mini_tasks = BreakdownUserTask.objects.all()
	print(all_mini_tasks)

	for each_mini_parent in all_mini_tasks:
		for each_mini_child in all_mini_tasks:
			if (each_mini_parent != each_mini_child and each_mini_parent.start_time == each_mini_child.start_time and each_mini_parent.end_time == each_mini_child.end_time):
				each_mini_child.delete()
				print("duplicate removed!")

	return HttpResponse("Allocated tasks successfully!")




'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to get army time and date format for create event
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def get_correct_date_time_format(request, day_num, clock_str):


    #Here what we need to do is parse out the day of and append the correct military time to match the UTC time conversion for the start and end time

    print("Day num is %s"%(day_num))

    ranges = get_current_week_range(request)

    print("ranges are "),
    print(ranges)

    #time inputs as 04 : 15 : PMZ

    #Get rid of the spaces within the string
    clock_str = clock_str.replace(' ', '')

    print("clock str after space replace is %s"%(clock_str))

    #Provide the appropriate offset for the conversion
    if 'am' in clock_str:
        clock_str = clock_str[0:4] + ' ' + 'AM'
        print("THIS IS AM!")
        print(clock_str)
    elif 'pm' in clock_str:
        clock_str = clock_str[0:4] + ' ' + 'PM' 
        print("THIS IS PM!")

    clock_str = datetime.datetime.strptime(clock_str, '%I:%M %p')
    clock_str = str(clock_str)
    clock_str = 'T'+clock_str[11:]

    print("Final clock_str is %s"%(clock_str))


    if (day_num == 'Monday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=0)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .
    elif (day_num == 'Tuesday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=1)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .
    elif (day_num == 'Wednesday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=2)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .
    elif (day_num == 'Thursday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=3)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .
    elif (day_num == 'Friday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=4)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .
    elif (day_num == 'Saturday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=5)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .
    elif (day_num == 'Sunday'):
        date_portion = parse(ranges[0]) + datetime.timedelta(days=6)
        date_portion = str(date_portion)
        date_portion = date_portion[0:10] #This is just the date now 2016-04-13 .

    completed_date_time = date_portion + clock_str
    print(completed_date_time)

    return completed_date_time



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Check Event Conflict Analysis With Other Tasks
-	User adds an event, this function controls the logic for 
	displaying the modal window with conflict data
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def event_conflict_analysis(request):

	if request.method == 'POST':
		print("checking event conflict analysis")
		
		#Get the post variable for the day
		day_to_check = request.POST.get('current_day')
		start_time = request.POST.get('start')
		end_time = request.POST.get('end')

		#Get some times to use from standard to military
		converted_start_time = get_correct_date_time_format(request, request.POST.get('current_day'), request.POST.get('start'))
		converted_end_time = get_correct_date_time_format(request, request.POST.get('current_day'), request.POST.get('end'))

		#Get a start and end date for the week
		ranges = get_current_week_range(request)

		#Push each day within the week to a list for easy selection
		week_list = []
		for days_iterator in range(0, 7):
			current_day = parse(ranges[0])
			current_day = current_day + datetime.timedelta(days=days_iterator)
			week_list.append(str(current_day))

		#POST var string to int conversion
		if (day_to_check == 'Monday'):
			day_to_check = 0
		elif (day_to_check == 'Tuesday'):
			day_to_check = 1
		elif (day_to_check == 'Wednesday'):
			day_to_check = 2
		elif (day_to_check == 'Thursday'):
			day_to_check = 3		
		elif (day_to_check == 'Friday'):
			day_to_check = 4
		elif (day_to_check == 'Saturday'):
			day_to_check = 5
		elif (day_to_check == 'Sunday'):
			day_to_check = 6

		#Parse object to string for character manipulation
		converted_start_time = str(converted_start_time)
		converted_end_time = str(converted_end_time)

		#Concatenate the correct day and time for the event to check event conflict analysis
		converted_start_time = week_list[day_to_check][0:10] + ' ' + converted_start_time[11:] + "+00:00"
		converted_end_time = week_list[day_to_check][0:10] + ' ' + converted_end_time[11:] + "+00:00"

		#Get all the user mini breakdown sets within a query set
		user_breakdown_mini_tasks = BUT.objects.filter(parent_task__authenticated_user = request.user, current_day=day_to_check)
		conflicts = []


		if (len(user_breakdown_mini_tasks) > 0):
			for each_breakdown_task in user_breakdown_mini_tasks:
				b_start = parse(each_breakdown_task.start_time)
				b_end = parse(each_breakdown_task.end_time)

				e_start = parse(converted_start_time)
				e_end = parse(converted_end_time)

				min_time_zeroed = ' 00:00:00+00:00'
				max_time_zeroed = ' 23:59:00+00:00'

				current_day_min= str(b_start)
				current_day_max= str(b_start)

				current_day_min += min_time_zeroed
				current_day_max += max_time_zeroed

				current_day_min = parse(current_day_min)
				current_day_max = parse(current_day_max)

				print(current_day_min)
				print("IS CURRENT DAY MIN!")

				print(current_day_max)
				print("IS CURRENT DAY MIN!")


				if ((e_start > current_day_min and e_end < current_day_max) and (e_start < b_start and e_end < b_start and e_start < b_end and e_end < b_end) or (e_start > b_start and e_end > b_start and e_start > b_end and e_end > b_end)):
					continue
				else:
					conflicts.append(each_breakdown_task)

		for tasks_breakdown in conflicts:
			print("Event conflicts with: %s"%(tasks_breakdown))


		if (len(user_breakdown_mini_tasks) > 0):
			data = serializers.serialize("json", conflicts)
			print(data)
			json.dumps(data)
		else:
			data = []
			data = serializers.serialize("json", data)
			json.dumps(data)

		return HttpResponse(data)
	else:
		print("not a post")
		return HttpResponse("Error, this is not a valid input response dingus")

