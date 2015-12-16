from __future__ import absolute_import
from __future__ import print_function
import datetime
import httplib2
import oauth2client
import argparse
import os
import logging
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

#Load the API key
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

#Set the API scope for the relevant API we are using and associated redirect path after validation
FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    redirect_uri='http://127.0.0.1:8000/oauth2callback')

#Main function deailing with auth verification
def index(request):
  storage = Storage(CredentialsModel, 'id', request.user, 'credential')
  credential = storage.get()
  if credential is None or credential.invalid == True:
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)

#User than calls the data function once authenticated
def auth_return(request):
  credential = FLOW.step2_exchange(request.REQUEST)
  storage = Storage(CredentialsModel, 'id', request.user, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/get_cal")

#Function to actually pull the data from the authenticated OAUTH user
def get_calendar_data(request):

    user_is_authenticated = False

    #Send request to pull data from the calendar API
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if not credential is None:

        user_is_authenticated = True
        http = httplib2.Http()
        http = credential.authorize(http)
        service = discovery.build('calendar', 'v3', http=http)
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

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

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        eventsResult = service.events().list(
            calendarId='primary', timeMin=now, maxResults=5, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(event['summary'])
            print_examples.append(str(event['summary']))


            context = {
                'user_cals' : user_cals,
                'print_examples' : print_examples,
                'user_is_authenticated' : user_is_authenticated
            }
            #This is the redirect URL that is sent to the user once the OAUTH credentials have been validated successfully
        return render(request, 'user_calendar.html', context)
    else:
        return render(request, 'user_calendar.html')

#Remove authorization manually (Oauth token removal)
def unauthorize_account(request):

    if request.method == "POST":
        entry = CredentialsModel.objects.get(id=request.user)
        entry.delete()
        return render(request, 'user_calendar.html')
    else:
        return render(request, 'user_calendar.html')
