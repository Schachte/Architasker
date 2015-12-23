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

from procrastinate import settings


def home(request):
    return render(request, 'home.html')

def tester_login_form(request):
    return render(request, 'login_form.html')
