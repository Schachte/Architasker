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
from store_new_events.models import UserEvent as SNE

#Load the API key
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

#Set the API scope for the relevant API we are using and associated redirect path after validation
FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    redirect_uri='http://127.0.0.1:8000/oauth2callback')

#These arrays temp. hold the user event data (is there a more efficient way of doing this??)
mon     = []
tues    = []
wed     = []
thurs   = []
fri     = []
sat     = []
sun     = []

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to convert unicode dictionaries into str dictionaries
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def convert(data):
    if isinstance(data, basestring):
        return str(data)
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
  current_user = User.objects.get(id=request.user.id)
  storage = Storage(CredentialsModel, 'id', current_user, 'credential')
  credential = storage.get()
  if credential is None or credential.invalid == True:
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user.id)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
User then calls the data function once authenticated
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def auth_return(request):
  credential = FLOW.step2_exchange(request.REQUEST)
  current_user = User.objects.get(id=request.user.id)
  storage = Storage(CredentialsModel, 'id', current_user, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/get_cal")

def patch_broken_pipe_error():
    """Monkey Patch BaseServer.handle_error to not write
    a stacktrace to stderr on broken pipe.
    http://stackoverflow.com/a/7913160"""
    import sys
    from SocketServer import BaseServer

    handle_error = BaseServer.handle_error

    def my_handle_error(self, request, client_address):
        type, err, tb = sys.exc_info()
        # there might be better ways to detect the specific erro
        if repr(err) == "error(32, 'Broken pipe')":
            # you may ignore it...
            logging.getLogger('mylog').warn(err)
        else:
            handle_error(self, request, client_address)

    BaseServer.handle_error = my_handle_error


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Custom function to parse out the user events and store them on-click
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def pull_user_event_data(request):
    user_is_authenticated = False

    #Send request to pull data from the calendar API
    current_user = User.objects.get(id=request.user.id)
    storage = Storage(CredentialsModel, 'id', current_user, 'credential')
    credential = storage.get()
    if not credential is None:

        '''Dealing with OAUTH verification'''
        user_is_authenticated = True
        http = httplib2.Http()
        http = credential.authorize(http)
        service = discovery.build('calendar', 'v3', http=http)

        '''These calculations below calculate the beginning of the week as well as the end of the week'''
        now = datetime.datetime.utcnow()
        now = now - datetime.timedelta(now.weekday())
        then = datetime.timedelta(days=6) #Indexed at 0
        then = now + then

        #Oauth handling var
        page_token = None

        #This is a shitty error-handling snippet for weirdly named calendars. We need to fix this
        calendar_list = service.calendarList().list(pageToken=page_token).execute()

        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            pass

        #Setting the beginning of the week as well as the end of the week
        # 'Z' indicates UTC time
        now = now.isoformat() + 'Z'
        then = then.isoformat() + 'Z'

        #Get the events off the primary calendar, this should be changed eventually so the user can select the calendar they please to use
        eventsResult = service.events().list(

            calendarId='primary', timeMin=now,
            timeMax=then).execute()

        events = eventsResult.get('items', [])

        #Get all the google events from the database when attempting the current sync
        google_tasks = SNE.objects.filter(is_google_task = True)

        #If they exist, then loop through and delete each one from the database
        if google_tasks is not None:
            for each_google_task in google_tasks:
                each_google_task.delete()

        #We need to start parsing and storing the data into the database with the most recent copy of google events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            string_converted_date = convert(event['start'])

            #Storing the physical event into the DB store
            if 'date' in string_converted_date.keys():
                current = str(string_converted_date['date'])
                dt = datetime.datetime.strptime(current, '%Y-%m-%d')

                current_user = User.objects.get(username=request.user.username)

                not_exists = False
                if not SNE.objects.filter(special_event_id=str(event['id'])).exists():
                    not_exists = True

                    temp_model = SNE.objects.create(
                        authenticated_user = current_user,
                        task_name = event['summary'],
                        is_google_task = True,
                        google_json = str(event),
                        start_time = str(now),
                        end_time = str(then),
                        special_event_id = str(event['id'])
                    )

                #Parsing out the different events to store into day arrays for the week
                if (dt.weekday() == 0 ):
                    mon.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Monday"
                        temp_model.save()

                elif (dt.weekday() == 1 ):
                    tues.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Tuesday"
                        temp_model.save()

                elif (dt.weekday() == 2 ):
                    wed.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Wednesday"
                        temp_model.save()

                elif (dt.weekday() == 3 ):
                    thurs.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Thursday"
                        temp_model.save()

                elif (dt.weekday() == 4 ):
                    fri.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Friday"
                        temp_model.save()

                elif (dt.weekday() == 5 ):
                    sat.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Saturday"
                        temp_model.save()

                elif (dt.weekday() == 6 ):
                    sun.append(convert(event))

                    if not_exists:
                        temp_model.current_day = "Sunday"
                        temp_model.save()


        return HttpResponseRedirect('/get_cal')


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to store new event created on calendar into database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def create_event(request):
    if request.method == 'POST':

        current_user = User.objects.get(id=request.user.id)
        temp_model = SNE.objects.create(
            authenticated_user = current_user,
            task_name = request.POST.get('text'),
            start_time = request.POST.get('start'),
            end_time = request.POST.get('end'),
            special_event_id = request.POST.get('id')
        )

        if (temp_model.start_time[0:3] == "Mon" ):
            #mon.append(temp_model)
            temp_model.current_day = "Monday"
                        
        elif (temp_model.start_time[0:3] == "Tue" ):
            #tues.append(temp_model)
            temp_model.current_day = "Tuesday"
        
        elif (temp_model.start_time[0:3] == "Wed" ):
            #wed.append(temp_model)
            temp_model.current_day = "Wednesday"

        elif (temp_model.start_time[0:3] == "Thu" ):
            #thurs.append(temp_model)
            temp_model.current_day = "Thursday"

        elif (temp_model.start_time[0:3] == "Fri" ):
            #fri.append(temp_model)
            temp_model.current_day = "Friday"

        elif (temp_model.start_time[0:3] == "Sat" ):
            print("Here")
            sat.append(temp_model)
            temp_model.current_day = "Saturday"              

        elif (temp_model.start_time[0:3] == "Sun" ):
            #sun.append(temp_model)
            temp_model.current_day = "Sunday"

        temp_model.save()
        print("done")

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to delete event from database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def delete_event(request):
    if request.method == 'POST':

        SNE.objects.filter(special_event_id=request.POST.get('id')).delete()
        print("deleted")

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to update event in database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def update_event(request):
    if request.method == 'POST':

        event = SNE.objects.get(special_event_id=request.POST.get('id'))
        event.task_name = request.POST.get('text')
        event.start_time = request.POST.get('start')
        event.end_time = request.POST.get('end')
        event.save()
        print("updated")


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to actually pull the data from the authenticated OAUTH user
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def get_calendar_data(request):

    #Authentication bool to verify Oauth steps have been completed
    user_is_authenticated = False

    #Send request to pull data from the calendar API
    current_user = User.objects.get(id=request.user.id)
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
        'event_length' : event_length
    }

    return render(request, 'calender.html', context)


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Remove authorization manually (Oauth token removal)
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def unauthorize_account(request):
    if request.method == "POST":
        entry = CredentialsModel.objects.get(id=request.user.id)
        entry.delete()
        return render(request, 'user_calendar.html')
    else:
        return render(request, 'user_calendar.html')
