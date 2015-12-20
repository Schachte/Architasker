from django.shortcuts import render
from django.template import loader, Context
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth import logout


def login_view(request):
    return render(request, 'login.html')

#View that requires the user to login to his/her account
def login_process(request):
    #Not sure this is a secure way of going about this....
    if 'user_name' in request.POST and 'pass_word' in request.POST:

        #Get POST params and validate the user credentials
        user = request.POST.get('user_name')
        password = request.POST.get('pass_word')
        user = authenticate(username=user, password=password)

        #Error handling for the user authentication
        if user is not None:
            if user.is_active:
                login(request, user)
            return HttpResponseRedirect('/get_cal')

        else:
            print('There was an error processing this login request')
            return HttpResponseRedirect('/login')
    else:
        print("Missing POST params")
        return HttpResponse("ERROR")

#Request handling the logout of the requested user
def logout_process(request):
    logout(request)
    return HttpResponseRedirect('/login')
