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
    service = build("plus", "v1", http=http)
    activities = service.activities()
    activitylist = activities.list(collection='public',
                                   userId='me').execute()
    logging.info(activitylist)

    return render_to_response('plus/welcome.html', {
                'activitylist': activitylist,
                })

def auth_return(request):
  if not xsrfutil.validate_token(settings.SECRET_KEY, request.GET['state'],
                                 request.user):
    return  HttpResponseBadRequest()
  credential = FLOW.step2_exchange(request.REQUEST)
  storage = Storage(CredentialsModel, 'id', request.user, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/")
