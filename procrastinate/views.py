from __future__ import absolute_import
from __future__ import print_function

from django.template import loader, Context
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect

from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
from procrastinate import settings
from apiclient import discovery
from django.core.cache import cache
from django.utils.cache import get_cache_key
import time
from app_account_management.models import UserExtended as UE
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.sessions.models import Session
from django.contrib.auth.backends import ModelBackend
import urlparse
import urllib
from app_account_management.models import UserExtended
from procrastinate import settings

def home(request):
    if not request.user:
        return render(request, 'HOME_PAGE/index.html')
    else:
        return HttpResponseRedirect('/dashboard')
