from __future__ import absolute_import
from __future__ import print_function
import datetime
import httplib2
import oauth2client
import argparse
import os
import logging
import collections
from django.template import loader, Context
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from .models import CredentialsModel
from apiclient.discovery import build
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
from procrastinate import settings
from apiclient import discovery
from django.core.cache import cache
from django.utils.cache import get_cache_key
import time

#Load the API key
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

#Set the API scope for the relevant API we are using and associated redirect path after validation
FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    redirect_uri='http://127.0.0.1:8000/oauth2callback')

mon     = []
tues    = []
wed     = []
thurs   = []
fri     = []
sat     = []
sun     = []

def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

#Main function deailing with auth verification
def index(request):
  storage = Storage(CredentialsModel, 'id', request.user.id, 'credential')
  credential = storage.get()
  if credential is None or credential.invalid == True:
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user.id)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)

#User than calls the data function once authenticated
def auth_return(request):
  credential = FLOW.step2_exchange(request.REQUEST)
  current_user = User.objects.get(id=request.user.id)
  storage = Storage(CredentialsModel, 'id', current_user, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/get_cal")

#Function to actually pull the data from the authenticated OAUTH user
def get_calendar_data(request):
    cache.delete('/get_cal')
    request.path = '/get_cal'
    key = get_cache_key(request)
    if cache.has_key(key):
        cache.delete(key)

    user_is_authenticated = False

    #Send request to pull data from the calendar API
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if not credential is None:

        user_is_authenticated = True
        http = httplib2.Http()
        http = credential.authorize(http)
        service = discovery.build('calendar', 'v3', http=http)

        '''These calculations below calculate the beginning of the week as well as the end of the week'''
        now = datetime.datetime.utcnow()
        now = now - datetime.timedelta(now.weekday())
        then = datetime.timedelta(days=6) #Indexed at 0
        then = now + then


        #Array to hold the different IDs associated with each calendar
        calendar_names = []

        page_token = None

        #Print the calendars
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if '@group' in str((calendar_list_entry['id'])) and not '#' in str((calendar_list_entry['id'])):
                calendar_names.append(str((calendar_list_entry['id'])))
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            pass

        for cals in calendar_names:
            print (str(cals))

        user_cals = []
        #Printing the names of the users calendars based on the ID
        for names in calendar_names:
            calendar_list_entry = service.calendarList().get(calendarId=names).execute()
            print (calendar_list_entry['summary'])
            user_cals.append(str(calendar_list_entry['summary']))

        print_examples = []

        #Setting the beginning of the week as well as the end of the week
        now = now.isoformat() + 'Z' # 'Z' indicates UTC time
        then = then.isoformat() + 'Z'

        eventsResult = service.events().list(
            calendarId='primary', timeMin=now,
            timeMax=then).execute()
        events = eventsResult.get('items', [])

        if not events:
            print('No upcoming events found.')
        time.sleep(1)
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            string_converted_date = convert(event['start'])
            # string_converted_date = string_converted_date['date']

            if 'date' in string_converted_date.keys():
                current = str(string_converted_date['date'])
                dt = datetime.datetime.strptime(current, '%Y-%m-%d')
                # print(int(dt))
                # print(dt.weekday())

                if (dt.weekday() == 0 and not convert(event) in mon):
                    mon.append(convert(event))
                elif (dt.weekday() == 1 and not convert(event) in tues):
                    tues.append(convert(event))
                elif (dt.weekday() == 2 and not convert(event) in wed):
                    wed.append(convert(event))
                elif (dt.weekday() == 3 and not convert(event) in thurs):
                    thurs.append(convert(event))
                elif (dt.weekday() == 4 and not convert(event) in fri):
                    fri.append(convert(event))
                elif (dt.weekday() == 5 and not convert(event) in sat):
                    sat.append(convert(event))
                elif (dt.weekday() == 6 and not convert(event) in sun):
                    sun.append(convert(event))

        if events:
            print('\n*********************************MONDAY TASKS*********************************\n')
            for monday_tasks in mon:
                string_converted_date = convert(monday_tasks['start'])
                print('Task: %s during the time of %s' %(monday_tasks['summary'], str(string_converted_date['date'])))

            print('\n*********************************TUESDAY TASKS*********************************\n')
            for tuesday_tasks in tues:
                string_converted_date = convert(tuesday_tasks['start'])
                print('Task: %s during the time of %s' %(tuesday_tasks['summary'], str(string_converted_date['date'])))

            print('\n*********************************WEDNESDAY TASKS*********************************\n')
            for wednesday_tasks in wed:
                string_converted_date = convert(wednesday_tasks['start'])
                print('Task: %s during the time of %s' %(wednesday_tasks['summary'], str(string_converted_date['date'])))

            print('\n*********************************THURSDAY TASKS*********************************\n')
            for thursday_tasks in thurs:
                string_converted_date = convert(thursday_tasks['start'])
                print('Task: %s during the time of %s' %(thursday_tasks['summary'], str(string_converted_date['date'])))

            print('\n*********************************FRIDAY TASKS*********************************\n')
            for friday_tasks in fri:
                string_converted_date = convert(friday_tasks['start'])
                print('Task: %s during the time of %s' %(friday_tasks['summary'], str(string_converted_date['date'])))

            print('\n*********************************SATURDAY TASKS*********************************\n')
            for saturday_tasks in sat:
                string_converted_date = convert(saturday_tasks['start'])
                print('Task: %s during the time of %s' %(saturday_tasks['summary'], str(string_converted_date['date'])))

            print('\n*********************************SUNDAY TASKS*********************************\n')
            for sunday_tasks in sun:
                string_converted_date = convert(sunday_tasks['start'])
                print('Task: %s during the time of %s' %(sunday_tasks['summary'], str(string_converted_date['date'])))

            print_examples.append(str(event['summary']))

        context = {
            'user_cals' : user_cals,
            'print_examples' : print_examples,
            'user_is_authenticated' : user_is_authenticated,
            'mon' : mon,
            'tues' : tues,
            'wed' : wed,
            'thurs' : thurs,
            'fri' : fri,
            'sat' : sat,
            'sun' : sun,
            'event_length' : len(events)
        }

        cache.delete('/get_cal')

            #This is the redirect URL that is sent to the user once the OAUTH credentials have been validated successfully
        return render(request, 'user_calendar.html', context)
    else:
        return render(request, 'user_calendar.html')

#Remove authorization manually (Oauth token removal)
def unauthorize_account(request):

    if request.method == "POST":
        entry = CredentialsModel.objects.get(id=request.user.id)
        entry.delete()
        return render(request, 'user_calendar.html')
    else:
        return render(request, 'user_calendar.html')
