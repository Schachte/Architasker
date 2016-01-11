from __future__ import absolute_import
from __future__ import print_function
import datetime
import httplib2
import oauth2client
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
from oauth2client import client
from oauth2client import tools
from apiclient.discovery import build
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
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

from .models import UserEvent as SNE
from .models import CredentialsModel
from procrastinate import settings
from app_account_management.models import UserExtended

#Load the API key
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

#Set the API scope for the relevant API we are using and associated redirect path after validation
FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    redirect_uri='http://127.0.0.1:8000/oauth2callback')



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


'''''''''''''''''''''''''''''''''''''''''''''''''''
Main function dealing with auth verification
'''''''''''''''''''''''''''''''''''''''''''''''''''

def index(request):
    current_user = User.objects.get(username=request.user.username)
    storage = Storage(CredentialsModel, 'id', current_user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user.id)
        logged_in_username = request.user.username
        user_data = {'var_test' : logged_in_username}
        pass_param = urllib.urlencode(user_data)
        FLOW.params['state']=pass_param
        authorize_url = FLOW.step1_get_authorize_url()
        pass_param = urllib.urlencode(user_data)
        state = pass_param
        return redirect(authorize_url, request)
    else:
        return HttpResponse("Already authorized")


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
User then calls the data function once authenticated
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def auth_return(request):

    #Get the currently logged in username
    user_variable_data = str(FLOW.params['state'])

    #get rid of the var_test= preprended text data for parsing reasons
    user_variable_data = user_variable_data[9:]

    #Get that user from the database in the form of a user object
    current_user = User.objects.get(username=user_variable_data)

    credential = FLOW.step2_exchange(request.REQUEST)

    storage = Storage(CredentialsModel, 'id', current_user, 'credential')
    storage.put(credential)

    user = authenticate(username=user_variable_data)
    login(request, user)

    user_extension_model = UserExtended.objects.get(authenticated_user=current_user)
    user_extension_model.google_auth = True
    user_extension_model.save()

    return HttpResponseRedirect("/dashboard")


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Custom function to parse out the user events and store them on-click
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#Current bug that the timed events are being ignored within the system
def pull_user_event_data(request):
    user_is_authenticated = False


    #Send request to pull data from the calendar API
    current_user = User.objects.get(id=request.user.id)
    current_user_ext = UserExtended.objects.get(authenticated_user=current_user)
    storage = Storage(CredentialsModel, 'id', current_user, 'credential')
    credential = storage.get()

    if not credential is None:

        '''Dealing with OAUTH verification'''
        user_is_authenticated = True
        http = httplib2.Http()
        http = credential.authorize(http)
        service = discovery.build('calendar', 'v3', http=http)

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

        now = current_BOW
        then = current_EOW #End of week for the current week

        #Oauth handling var
        page_token = None

        #This is a shitty error-handling snippet for weirdly named calendars. We need to fix this
        calendar_list = service.calendarList().list(pageToken=page_token).execute()

        #Deal with authentication and storing user auth data
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            pass

        #Setting the beginning of the week as well as the end of the week
        # 'Z' indicates UTC time
        now = now.isoformat() + 'Z'
        then = then.isoformat() + 'Z'

        now = str(now[0:10]) + 'T00:00:01Z'
        then = str(then[0:10]) + 'T23:59:59Z'

        #Get the events off the primary calendar, this should be changed eventually so the user can select the calendar they please to use
        eventsResult = service.events().list(

            calendarId='primary', timeMin=now,
            timeMax=then, maxResults=1500).execute()

        events = eventsResult.get('items', [])

        #Get all the google events from the database when attempting the current sync
        google_tasks = SNE.objects.filter(is_google_task = True)

        #generating start and end of time range for the week
        start_range = datetime.datetime.strptime(now[0:10], '%Y-%m-%d')
        end_range = datetime.datetime.strptime(then[0:10], '%Y-%m-%d')

        #Item that we will append if the boolean val is flipped
        multiple_recurrences_in_a_week      = False

        current_month_needs_to_be_replaced  = False
        current_month_day_to_replace_start  = None
        current_year_to_replace_start       = None
        current_month_to_replace_start      = None

        #This array will house mutliple events if (multiple_recurrences_in_a_week) == True
        current_month_day_to_replace_start_array    = []
        current_year_to_replace_start_array         = []
        current_month_to_replace_start_array        = []

        #This is the dictionary that will house a relation between the date (month day) along with the day of the week for the current week we live in
        day_date_data_start = {}

        #This is a simple array to loop through to make indexed associations
        week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        #shitty counter var to increment on each loop pass
        week_day_iterator = 0

        #Loop through each of the dates inside of the range of the start and end date range
        for single_date in (start_range + datetime.timedelta(n) for n in range(7)):

            #Current day of the month will represent a string for the looping var
            current_day_of_month = str(single_date)

            #Append it to the dictionary
            day_date_data_start[week_days[week_day_iterator]] = current_day_of_month[0:10].replace('-', '')

            #increment the counter
            week_day_iterator+=1

        '''
        ACCOUNT FOR THE END RANGES NOW
        '''

        #deleting tasks only for the current week
        if google_tasks is not None:
            for task in google_tasks:
                task_start_time = convert(task.start_time)
                task_start_time = datetime.datetime.strptime(task_start_time[0:10], '%Y-%m-%d')

                if task_start_time >= start_range and task_start_time <= end_range:
                    task.delete()

        #We need to start parsing and storing the data into the database with the most recent copy of google events
        for event in events:
            current_month_needs_to_be_replaced = False

            #Lets check recurrence
            event = convert(event)

            #Check if the current event we are dealing with is a recurring event
            if 'recurrence' in event:
                print(event['recurrence'])

                #Get the data inside the recurrence array in the event dictionary
                for each_item in event['recurrence']:

                    #If there is a BYDAY repetition, then regex parse the data to get the days
                    if ("BYDAY=" in each_item):
                        current_month_needs_to_be_replaced = True

                        '''REGEX START'''

                        match_pattern   = r'(BYDAY=([\w,-]+))'
                        match_string    = str(each_item)
                        match = re.search(match_pattern, match_string)

                        print("EACH ITEM IS " + each_item)
                        print("match is " + str(match))

                        #This piece gets rid of the BYDAY= part
                        days = match.group(0)[6:]

                        '''REGEX END'''

                        #Convert the regex data into a list seaparted by commas
                        days = days.split(',')
                        print(days),
                        print(' are the days')

                        #Go in and find/parse all the day abbreviations from Google into day names into array information
                        days_list_conversion = []

                        '''
                        Ok, so here by day exists, so we need to use hte two dates to find the time delta for the dates of the month
                        '''
                        print("length of days is %d for %s"%(len(days), event['summary']))
                        counter = 0
                        for each_day in days:

                            if (counter > len(days)):
                                break

                            #Some days prepend with integer, so here I am stripping out the integer
                            each_day = ''.join([i for i in each_day if not i.isdigit()])
                            if '-' in each_day:
                                each_day = each_day.replace('-', '')

                            if each_day == 'SU':
                                days_list_conversion.append('Sunday')
                            elif each_day == 'MO':
                                days_list_conversion.append('Monday')
                            elif each_day == 'TU':
                                days_list_conversion.append('Tuesday')
                            elif each_day == 'WE':
                                days_list_conversion.append('Wednesday')
                            elif each_day == 'TH':
                                days_list_conversion.append('Thursday')
                            elif each_day == 'FR':
                                days_list_conversion.append('Friday')
                            elif each_day == 'SA':
                                days_list_conversion.append('Saturday')
                            counter+=1

                        #LETS DO SOME LOGIC TO CHECK IF THERE ARE MULTIPLE RECURRENCES INSIDE OF A SINGLE WEEK
                        if (len(days_list_conversion) > 1):
                            multiple_recurrences_in_a_week = True

                            days_counter = 0
                            print("length of days_list_conversion is %s"%(len(days_list_conversion)))
                            print(days_list_conversion)
                            for days in days_list_conversion:
                                print(day_date_data_start[days_list_conversion[days_counter]][6:])
                                current_month_day_to_replace_start_array.append(day_date_data_start[days_list_conversion[days_counter]][6:])
                                current_year_to_replace_start_array.append(day_date_data_start[days_list_conversion[days_counter]][0:4])
                                current_month_to_replace_start_array.append(day_date_data_start[days_list_conversion[days_counter]][4:6])
                                days_counter+=1
                            print(current_month_day_to_replace_start_array, current_year_to_replace_start_array, current_month_to_replace_start_array)
                        else:
                            current_month_day_to_replace_start    = day_date_data_start[days_list_conversion[0]][6:]
                            current_year_to_replace_start         = day_date_data_start[days_list_conversion[0]][0:4]
                            current_month_to_replace_start        = day_date_data_start[days_list_conversion[0]][4:6]

                    #If this is a monthly recurring event without the BYDAY= distingusher then grab the day it repeats on in the month
                    elif ("FREQ=MONTHLY" in each_item):
                        current_month_needs_to_be_replaced = True

                        #If it occurs monthly and no day is present, get the day of the monthy recurrence item
                        if 'dateTime' in event['start']:
                            date_object = str(parse(event['start']['dateTime']))
                        else:
                            date_object = str(parse(event['start']['date']))

                        for key, value in day_date_data_start.iteritems():
                            if (str(value[6:]) == str(date_object[8:10])):
                                current_month_day_to_replace_start = str(date_object[8:10])
                                current_year_to_replace_start = str(value[0:4])
                                current_month_to_replace_start = str(value[4:6])
                                break

                        # #LETS DO SOME LOGIC TO CHECK IF THERE ARE MULTIPLE RECURRENCES INSIDE OF A SINGLE WEEK
                        # if (len(days_list_conversion) > 1):
                        #     multiple_recurrences_in_a_week = True

            # try:
            string_converted_date = convert(event['start'])
            string_converted_end = convert(event['end'])
            string_colors = convert(event)

            #Storing the physical event into the DB store
            if multiple_recurrences_in_a_week:

                recurrence_data_length = len(current_month_day_to_replace_start_array)
                print("recurrence length is %d" %(recurrence_data_length))

                for recurrence_data in range(0, recurrence_data_length):

                    if 'date' in string_converted_date.keys() or 'dateTime' in  string_converted_date.keys():

                        if 'dateTime' in string_converted_date.keys():
                            current = str(string_converted_date['dateTime'])
                            times = current[11:]
                            dt = datetime.datetime.strptime(current, '%Y-%m-%dT' + times)
                            current = current[0:19]

                            #This is where we are going to get the end time for the ending date after conversion
                            ending_date = int(event['end']['dateTime'][8:10])

                            starting_date = int(event['start']['dateTime'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date

                            current = str(current_year_to_replace_start_array[recurrence_data]) + '-' + str(current_month_to_replace_start_array[recurrence_data]) + '-' + str(current_month_day_to_replace_start_array[recurrence_data]) + current[10:]

                        elif 'date' in string_converted_date.keys():

                            current = str(string_converted_date['date'])
                            dt = datetime.datetime.strptime(current, '%Y-%m-%d')

                            current = current[0:10] + 'T00:00:00Z'
                            # if (current_month_needs_to_be_replaced == True):
                            current = str(current_year_to_replace_start_array[recurrence_data]) + '-' + str(current_month_to_replace_start_array[recurrence_data]) + '-' + str(current_month_day_to_replace_start_array[recurrence_data]) + 'T00:00:00Z'

                            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                            Begin calculating the time delta for the beginning and ending times of the event
                            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                            ending_date = int(event['end']['date'][8:10])
                            starting_date = int(event['start']['date'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date

                            #initiate the conversion for the non-time events
                            current_date_conversion = parse(current)

                            end_time = current_date_conversion + datetime.timedelta(days=time_delta)
                            end_time = str(end_time)

                        if 'dateTime' in string_converted_end.keys():
                            end_time = str(string_converted_end['dateTime'])
                            end_time = end_time[0:19]
                            end_time_holder = end_time[10:]
                            print(str(end_time) + " is the endtime before the conversion")

                            # if (current_month_needs_to_be_replaced == True):
                            current = str(string_converted_date['dateTime'])
                            times = current[11:]
                            dt = datetime.datetime.strptime(current, '%Y-%m-%dT' + times)
                            current = current[0:19]

                            ending_date = int(event['end']['dateTime'][8:10])
                            starting_date = int(event['start']['dateTime'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date
                            current = str(current_year_to_replace_start_array[recurrence_data]) + '-' + str(current_month_to_replace_start_array[recurrence_data]) + '-' + str(current_month_day_to_replace_start_array[recurrence_data]) + current[10:]

                            #Convert the string version of the date into a dateTime object to do timeDelta calculations on
                            current_date_conversion = parse(current)
                            #datetime.timedelta(days=10)
                            end_time = current_date_conversion + datetime.timedelta(days=time_delta)
                            end_time = str(end_time)
                            end_time = end_time.replace(' ', 'T')
                            end_time = end_time[0:10] + end_time_holder
                            # end_time = parse(end_time)
                            print(str(end_time) + " is the end time after conversion.")

                        elif 'date' in string_converted_end.keys():
                            end_time = str(string_converted_end['date'])
                            #appends T00:00:00Z to the end of the end date
                            end_time = end_time[0:10] + 'T00:00:00Z'

                            '''
                            Begin calculating the time delta for the beginning and ending times of the event
                            '''
                            ending_date = int(event['end']['date'][8:10])
                            starting_date = int(event['start']['date'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date

                            #initiate the conversion for the non-time events
                            current_date_conversion = parse(current)

                            end_time = current_date_conversion + datetime.timedelta(days=time_delta)
                            end_time = str(end_time)
                            end_time = end_time.replace(' ', 'T')
                            # end_time = parse(end_time)
                            print(str(end_time) + " is the end time after conversion. for DATE")

                        current_user = User.objects.get(username=request.user.username)
                        end_time = str(end_time)

                        #This is an error-handling check to see if the time is formatted incorrectly
                        if ('+' in str(end_time)):

                            #convert to a string object
                            end_time = str(end_time)
                            end_time = str(end_time[0:10])
                            end_time = end_time + 'T00:00:00Z'

                            #Convert back to a datetime object
                        # end_time = parse(end_time)


                        current = str(current)

                        #Check if the UTC version of the current time has been persisted properly
                        if 'Z' not in current:
                            current = current + 'Z'

                        if 'Z' not in end_time:
                            end_time = end_time + 'Z'

                        print('Event is ' + event['summary'])
                        print('Start time is ' + str(current))
                        print('End time is ' + str(end_time))

                        not_exists = False


                        HEX_ASSOCIATION = {
                            '1': '#AEA8D3', '2': '#87D37C', '3': '#BE90D4', '4': '#E26A6A', '5': '#F9BF3B', '6': '#EB974E', '7': '#19B5FE', '8': '#D2D7D3', '9': '#4B77BE', '10': '#26A65B',
                            '11': '#D24D57'
                        }

                        if not SNE.objects.filter(task_name = event['summary'], start_time = str(current), end_time = str(end_time)).exists():
                            not_exists = True

                            temp_model = SNE.objects.create(
                                authenticated_user = current_user,
                                task_name = event['summary'],
                                is_google_task = True,
                                google_json = str(event),
                                start_time = str(current),
                                end_time = str(end_time),
                                special_event_id = str(event['id']) + str(randint(0, 193453))
                            )
                        else:
                            SNE.objects.filter(task_name = event['summary'], start_time = str(current), end_time = str(end_time)).update(color = HEX_ASSOCIATION[event['colorId']])



                        if 'colorId' in event and not_exists:
                            temp_model.color = HEX_ASSOCIATION[event['colorId']]
                        elif not 'colorId' in event and not_exists:
                            temp_model.color = HEX_ASSOCIATION['1']


                        '''
                        I DONT ACUTALLY KNOW IF THE CODE BELOW IS ANY GOOD FOR RECURRING BASED-EVENTS
                        '''

                        #Parsing out the different events to store into day arrays for the week
                        if (dt.weekday() == 0 ):

                            if not_exists:
                                temp_model.current_day = "Monday"
                                temp_model.save()

                        elif (dt.weekday() == 1 ):


                            if not_exists:
                                temp_model.current_day = "Tuesday"
                                temp_model.save()

                        elif (dt.weekday() == 2 ):

                            if not_exists:
                                temp_model.current_day = "Wednesday"
                                temp_model.save()

                        elif (dt.weekday() == 3 ):

                            if not_exists:
                                temp_model.current_day = "Thursday"
                                temp_model.save()

                        elif (dt.weekday() == 4 ):

                            if not_exists:
                                temp_model.current_day = "Friday"
                                temp_model.save()

                        elif (dt.weekday() == 5 ):

                            if not_exists:
                                temp_model.current_day = "Saturday"
                                temp_model.save()

                        elif (dt.weekday() == 6 ):

                            if not_exists:
                                temp_model.current_day = "Sunday"
                                temp_model.save()

                        else:
                            temp_model.current_day = "Monday"
                            temp_model.save()
                    multiple_recurrences_in_a_week = False

                current_month_day_to_replace_start_array = []
                current_year_to_replace_start_array = []
                current_month_to_replace_start_array = []
            else:
                if 'date' in string_converted_date.keys() or 'dateTime' in  string_converted_date.keys():

                    if 'dateTime' in string_converted_date.keys():
                        current = str(string_converted_date['dateTime'])
                        times = current[11:]
                        dt = datetime.datetime.strptime(current, '%Y-%m-%dT' + times)
                        current = current[0:19]

                        #This is where we are going to get the end time for the ending date after conversion
                        ending_date = int(event['end']['dateTime'][8:10])
                        starting_date = int(event['start']['dateTime'][8:10])

                        #This will help us find the number of days past the start date to calculate the correct time converison for the event
                        time_delta = ending_date - starting_date

                        if (current_month_needs_to_be_replaced == True):
                            current = str(current_year_to_replace_start) + '-' + str(current_month_to_replace_start) + '-' + str(current_month_day_to_replace_start) + current[10:]

                            #Convert the string version of the date into a dateTime object to do timeDelta calculations on
                            current_date_conversion = parse(current)

                            end_date_conversion = current_date_conversion + datetime.timedelta(days=time_delta)


                    elif 'date' in string_converted_date.keys():

                        current = str(string_converted_date['date'])
                        dt = datetime.datetime.strptime(current, '%Y-%m-%d')

                        #appends T00:00:00Z to the end of the start date
                        #This is how dhtmlxscheduler defines an all day event
                        current = current[0:10] + 'T00:00:00Z'
                        if (current_month_needs_to_be_replaced == True):
                            current = str(current_year_to_replace_start) + '-' + str(current_month_to_replace_start) + '-' + str(current_month_day_to_replace_start) + 'T00:00:00Z'

                            '''
                            Begin calculating the time delta for the beginning and ending times of the event
                            '''

                            end_time = str(string_converted_end['date'])
                            #appends T00:00:00Z to the end of the end date
                            end_time = end_time[0:10] + 'T00:00:00Z'

                            '''
                            Begin calculating the time delta for the beginning and ending times of the event
                            '''
                            ending_date = int(event['end']['date'][8:10])
                            starting_date = int(event['start']['date'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date

                            #initiate the conversion for the non-time events
                            current_date_conversion = parse(current)

                            end_time = current_date_conversion + datetime.timedelta(days=time_delta)
                            end_time = str(end_time)
                            end_time = end_time.replace(' ', 'T')
                            # end_time = parse(end_time)

                    if 'dateTime' in string_converted_end.keys():
                        end_time = str(string_converted_end['dateTime'])
                        end_time = end_time[0:19]
                        end_time_holder = end_time[10:]

                        if (current_month_needs_to_be_replaced == True):
                            current = str(string_converted_date['dateTime'])
                            times = current[11:]
                            dt = datetime.datetime.strptime(current, '%Y-%m-%dT' + times)
                            current = current[0:19]

                            ending_date = int(event['end']['dateTime'][8:10])
                            starting_date = int(event['start']['dateTime'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date
                            current = str(current_year_to_replace_start) + '-' + str(current_month_to_replace_start) + '-' + str(current_month_day_to_replace_start) + current[10:]

                            #Convert the string version of the date into a dateTime object to do timeDelta calculations on
                            current_date_conversion = parse(current)

                            end_time = current_date_conversion + datetime.timedelta(days=time_delta)
                            end_time = str(end_time)
                            end_time = end_time.replace(' ', 'T')
                            end_time = end_time[0:10] + end_time_holder


                    elif 'date' in string_converted_end.keys():
                        end_time = str(string_converted_end['date'])
                        #appends T00:00:00Z to the end of the end date
                        end_time = end_time[0:10] + 'T00:00:00Z'

                        if (current_month_needs_to_be_replaced == True):
                            '''
                            Begin calculating the time delta for the beginning and ending times of the event
                            '''
                            end_time = str(string_converted_end['date'])
                            #appends T00:00:00Z to the end of the end date
                            end_time = end_time[0:10] + 'T00:00:00Z'


                            '''
                            Begin calculating the time delta for the beginning and ending times of the event
                            '''
                            ending_date = int(event['end']['date'][8:10])
                            starting_date = int(event['start']['date'][8:10])

                            #This will help us find the number of days past the start date to calculate the correct time converison for the event
                            time_delta = ending_date - starting_date

                            #initiate the conversion for the non-time events
                            current_date_conversion = parse(current)

                            end_time = current_date_conversion + datetime.timedelta(days=time_delta)
                            end_time = str(end_time)
                            end_time = end_time.replace(' ', 'T')
                            # end_time = parse(end_time)

                    current_user = User.objects.get(username=request.user.username)

                    end_time = str(end_time)
                    #This is an error-handling check to see if the time is formatted incorrectly
                    if ('+' in str(end_time)):
                        #Then the end time is formatted incorrectly

                        #convert to a string object
                        end_time = str(end_time)
                        end_time = str(end_time[0:10])
                        end_time = end_time + 'T00:00:00Z'

                    current = str(current)

                    #Check if the UTC version of the current time has been persisted properly
                    if 'Z' not in current:
                        current = current + 'Z'

                    if 'Z' not in end_time:
                        end_time = end_time + 'Z'

                    print("IN THE ELSE------")
                    print('Event is ' + event['summary'])
                    print('Start time is ' + str(current))
                    print('End time iszz ' + str(end_time))


                    not_exists = False

                    HEX_ASSOCIATION = {
                        '1': '#AEA8D3', '2': '#87D37C', '3': '#BE90D4', '4': '#E26A6A', '5': '#F9BF3B', '6': '#EB974E', '7': '#19B5FE', '8': '#D2D7D3', '9': '#4B77BE', '10': '#26A65B',
                        '11': '#D24D57'
                    }

                    if not SNE.objects.filter(task_name = event['summary'], start_time = str(current), end_time = str(end_time)).exists():
                        not_exists = True

                        temp_model = SNE.objects.create(
                            authenticated_user = current_user,
                            task_name = event['summary'],
                            is_google_task = True,
                            google_json = str(event),
                            start_time = str(current),
                            end_time = str(end_time),
                            special_event_id = str(event['id'])
                        )
                        print("We are going to save the model where start time is " + str(current))
                        # temp_model.save
                    else:
                        SNE.objects.filter(task_name = event['summary'], start_time = str(current), end_time = str(end_time)).update(color = HEX_ASSOCIATION[event['colorId']])
                        # break


                    if 'colorId' in event and not_exists:
                        temp_model.color = HEX_ASSOCIATION[event['colorId']]
                    elif not 'colorId' in event and not_exists:
                        temp_model.color = HEX_ASSOCIATION['1']


                    '''
                    I DONT ACUTALLY KNOW IF THE CODE BELOW IS ANY GOOD FOR RECURRING BASED-EVENTS
                    '''

                    #Parsing out the different events to store into day arrays for the week
                    if (dt.weekday() == 0 ):

                        if not_exists:
                            temp_model.current_day = "Monday"
                            temp_model.save()

                    elif (dt.weekday() == 1 ):

                        if not_exists:
                            temp_model.current_day = "Tuesday"
                            temp_model.save()

                    elif (dt.weekday() == 2 ):

                        if not_exists:
                            temp_model.current_day = "Wednesday"
                            temp_model.save()

                    elif (dt.weekday() == 3 ):

                        if not_exists:
                            temp_model.current_day = "Thursday"
                            temp_model.save()

                    elif (dt.weekday() == 4 ):

                        if not_exists:
                            temp_model.current_day = "Friday"
                            temp_model.save()

                    elif (dt.weekday() == 5 ):

                        if not_exists:
                            temp_model.current_day = "Saturday"
                            temp_model.save()

                    elif (dt.weekday() == 6 ):

                        if not_exists:
                            temp_model.current_day = "Sunday"
                            temp_model.save()

                    else:
                        temp_model.current_day = "Monday"
                        temp_model.save()


                current_month_day_to_replace_start_array = []
                current_year_to_replace_start_array = []
                current_month_to_replace_start_array = []

        extension_model = UserExtended.objects.get(authenticated_user=request.user)
        extension_model.google_auth = True
        extension_model.save()

    return HttpResponseRedirect('/dashboard')


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to store new event created on calendar into database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
@login_required(login_url='/login')
def create_event(request):
    if request.method == 'POST':

        current_user = User.objects.get(id=request.user.id)
        temp_model = SNE.objects.create(
            authenticated_user = current_user,
            task_name = request.POST.get('text'),
            start_time = request.POST.get('start'),
            end_time = request.POST.get('end'),
            special_event_id = request.POST.get('id'),
            color = '#34495e'
        )

        if (request.POST.get('weekday') == "Mon" ):
            temp_model.current_day = "Monday"

        elif (request.POST.get('weekday') == "Tue" ):
            temp_model.current_day = "Tuesday"

        elif (request.POST.get('weekday') == "Wed" ):
            temp_model.current_day = "Wednesday"

        elif (request.POST.get('weekday') == "Thu" ):
            temp_model.current_day = "Thursday"

        elif (request.POST.get('weekday') == "Fri" ):
            temp_model.current_day = "Friday"

        elif (request.POST.get('weekday') == "Sat" ):
            temp_model.current_day = "Saturday"

        elif (request.POST.get('weekday') == "Sun" ):
            temp_model.current_day = "Sunday"

        temp_model.save()
    return HttpResponse("none")

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to delete event from database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
@login_required(login_url='/login')
def delete_event(request):
    print("before if")
    if request.method == 'POST':
        print("right before delete")
        SNE.objects.get(special_event_id=request.POST.get('id')).delete()
        print("deleted")
        return HttpResponse("deleted")



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to update event in database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def update_event(request):

    if request.method == 'POST':
        data_dict = convert(request.POST)
        EVENT_ID = data_dict['id']
        TASK_NAME = data_dict['text']
        TASK_NAME = str(TASK_NAME)
        if 'color' in request.POST:
            COLOR_NAME = str(data_dict['color'])
        if SNE.objects.filter(special_event_id=EVENT_ID).exists():

            event_task = SNE.objects.filter(
            special_event_id=EVENT_ID).update(
                task_name=data_dict['text'],
                start_time = data_dict['start'],
                end_time = data_dict['end']
                )

            if 'color' in request.POST:
                event_task = SNE.objects.filter(
                special_event_id=EVENT_ID).update(color=COLOR_NAME)

            return HttpResponse("true")
        else:
            print("false")
            return HttpResponse("none")



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to actually pull the data from the authenticated OAUTH user
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
@login_required(login_url='/login')
def get_calendar_data(request):


    current_user            = User.objects.get(username=request.user.username)
    current_user_extended   = UserExtended.objects.get(authenticated_user=current_user)
    current_user_time_zone  = current_user_extended.time_zone

    if (not current_user_time_zone == 'None'):
        print(current_user_time_zone)
        my_date                 = datetime.datetime.now(pytz.timezone(current_user_time_zone))
        user_day_of_week        = my_date.day


    #Authentication bool to verify Oauth steps have been completed
    user_is_authenticated = False
    user_login_count = True
    user_initial_setup = False
    google_auth_complete = False

    #Send request to pull data from the calendar API
    current_user = User.objects.get(username=request.user.username)
    extended_user = UserExtended.objects.get(authenticated_user=current_user)

    if (extended_user.user_login_count > 0):
        user_login_count = True
    else:
        user_login_count = False

    if (extended_user.initial_setup_complete == False):
        user_initial_setup = False
    else:
        user_initial_setup = True

    if (extended_user.google_auth == False):
        google_auth_complete = False
    else:
        google_auth_complete = True


    storage = Storage(CredentialsModel, 'id', current_user, 'credential')
    credential = storage.get()
    if not credential is None:
        user_is_authenticated = True
        event_length = SNE.objects.all().count()
    else:
        event_length = 0

    context = {

        'user_is_authenticated' : user_is_authenticated,
        'mon' : SNE.objects.filter(current_day = 'Monday'),
        'tues' : SNE.objects.filter(current_day = 'Tuesday'),
        'wed' : SNE.objects.filter(current_day = 'Wednesday'),
        'thurs' : SNE.objects.filter(current_day = 'Thursday'),
        'fri' : SNE.objects.filter(current_day = 'Friday'),
        'sat' : SNE.objects.filter(current_day = 'Saturday'),
        'sun' : SNE.objects.filter(current_day = 'Sunday'),
        'event_length' : event_length,
        'current_user' : request.user.username,
        'first_name' : request.user.first_name,
        'last_name' : request.user.last_name,
        'user_login_count' : user_login_count,
        'user_initial_setup' : user_initial_setup,
        'google_auth_complete' : google_auth_complete,
    }

    if (not current_user_time_zone == 'None'):
        context['user_day_of_week'] = user_day_of_week

    return render(request, 'DASHBOARD_PAGE/index.html', context)

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Remove authorization manually (Oauth token removal)
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
@login_required(login_url='/login')
def unauthorize_account(request):
    if request.method == "POST":
        entry = CredentialsModel.objects.get(id=request.user.id)
        entry.delete()
        return render(request, 'user_calendar.html')
    else:
        return render(request, 'user_calendar.html')
