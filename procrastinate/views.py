from __future__ import absolute_import
from __future__ import print_function
from django.template import loader, Context
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.shortcuts import render
import datetime
import httplib2
import os
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import argparse
# flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

from django.contrib.auth.models import User
from oauth2client.django_orm import Storage
from .models import CredentialsModel
import os
import logging
import httplib2

from apiclient.discovery import build
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
from procrastinate import settings
from apiclient import discovery

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

print (CLIENT_SECRETS)

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    redirect_uri='http://127.0.0.1:8000/oauth2callback')

def index(request):
  storage = Storage(CredentialsModel, 'id', request.user, 'credential')
  credential = storage.get()
  if credential is None or credential.invalid == True:
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user)

    print (FLOW.params['state'])
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)
  else:
    http = httplib2.Http()
    http = credential.authorize(http)
    service = discovery.build('calendar', 'v3', http=http)
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    #Code below is designed to purely test the functionality of the grabbing of the user calendar entries

    #Array to hold the different IDs associated with each calendar
    calendar_names = []

    page_token = None
    while True:
      calendar_list = service.calendarList().list(pageToken=page_token).execute()
      for calendar_list_entry in calendar_list['items']:
        calendar_names.append(str((calendar_list_entry['id'])))
      page_token = calendar_list.get('nextPageToken')
      if not page_token:
        break

    #Printing the names of the users calendars based on the ID
    for names in calendar_names:
        calendar_list_entry = service.calendarList().get(calendarId=names).execute()
        print (calendar_list_entry['summary'])

        #This is the redirect URL that is sent to the user once the OAUTH credentials have been validated successfully
    return HttpResponseRedirect("/admin")

def auth_return(request):

    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    I don't know what the hell this code is doing, but it breaks the response like 50% of the time
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  # if not xsrfutil.validate_token(settings.SECRET_KEY, request.GET['state'],
  #                                request.user):
  #   return  HttpResponseBadRequest()
  credential = FLOW.step2_exchange(request.REQUEST)
  storage = Storage(CredentialsModel, 'id', request.user, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/admin")
