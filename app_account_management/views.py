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
from .models import UserExtended
from app_calendar.models import UserEvent
from django.template.loader import render_to_string
import json

from app_review.models import ReviewModel as Review


def login_view(request):
    if not request.user.username:
        return render(request, 'HOME_PAGE/login.html')
    else:
        return HttpResponseRedirect('/dashboard')

def register_view(request):
    if not request.user.username:
        return render(request, 'HOME_PAGE/register.html')
    else:
        return HttpResponseRedirect('/dashboard')

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
                UE_model = UserExtended.objects.get(authenticated_user=user)
                UE_model.user_login_count += 1
                UE_model.save()
            return HttpResponseRedirect('/dashboard')

        else:
            print('There was an error processing this login request')
            return HttpResponseRedirect('/login')
    else:
        print("Missing POST params")
        return HttpResponse("ERROR")

#View that requires the user to login to his/her account
def processor_register(request):
    #Not sure this is a secure way of going about this....
    if request.method == "POST":
        if 'first_name' in request.POST:
            if request.POST.get('first_name') == '':
                data = {}
                data['return_error'] = 'First Name is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
        if 'last_name' in request.POST:
            if request.POST.get('last_name') == '':
                data = {}
                data['return_error'] = 'Last Name is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
        if 'dob' in request.POST:
            if request.POST.get('dob') == '':
                data = {}
                data['return_error'] = 'Date of Birth is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
        if 'user_name' in request.POST:
            if request.POST.get('user_name') == '':
                data = {}
                data['return_error'] = 'User Name is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
            elif len(request.POST.get('user_name')) < 6:
                data = {}
                data['return_error'] = 'Please enter a username greater than 6 characters!'
                return HttpResponse(json.dumps(data), content_type = "application/json")

        if 'user_email' in request.POST:
            if request.POST.get('user_email') == '':
                data = {}
                data['return_error'] = 'Error: Email is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
            elif not '@' in request.POST.get('user_email') or not '.com' in request.POST.get('user_email'):
                data = {}
                data['return_error'] = 'Error: Email is Invalid!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
        if 'pass_word' in request.POST:
            print("here")
            if request.POST.get('pass_word') == '':
                data = {}
                data['return_error'] = 'Error: Password Intial is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")
        if 'pass_word2' in request.POST:
            print("here2")
            if request.POST.get('pass_word2') == '':
                data = {}
                data['return_error'] = 'Error: Password Verify is Missing!'
                return HttpResponse(json.dumps(data), content_type = "application/json")

        if (not str(request.POST.get('pass_word')) == str(request.POST.get('pass_word2'))):
                data = {}
                data['return_error'] = 'Error: Passwords Don\'t Match!'
                return HttpResponse(json.dumps(data), content_type = "application/json")

        if (User.objects.filter(username=request.POST.get('user_name')).exists()):
            data = {}
            data['return_error'] = 'Error: User Already Exists!'
            return HttpResponse(json.dumps(data), content_type = "application/json")

        if (User.objects.filter(email=request.POST.get('user_email')).exists()):
            data = {}
            data['return_error'] = 'Error: Email Already In-Use!'
            return HttpResponse(json.dumps(data), content_type = "application/json")

        new_user = User.objects.create(

            username = request.POST.get('user_name'),
            first_name = request.POST.get('first_name'),
            last_name = request.POST.get('last_name'),
            email = request.POST.get('user_email'),
        )
        new_user.set_password(request.POST.get('pass_word'))
        new_user.save()

        new_user_extended = UserExtended.objects.create(
            authenticated_user = new_user,
            dob = request.POST.get('dob'),
        )
        new_user_extended.save()

        user = authenticate(username=request.POST.get('user_name'))

        login(request, user)

        data = {}
        data['return_error'] = 'successor'
        return HttpResponse(json.dumps(data), content_type = "application/json")
    else:
        return HttpResponse("Error")

#Request handling the logout of the requested user
def logout_process(request):
    logout(request)
    return HttpResponseRedirect('/login')

#Need to hook up a button for this
def clear_google_tasks(request):
    user_google_tasks = UserEvent.objects.filter(authenticated_user=request.user, is_google_task=True).all()
    for each_event in user_google_tasks:
        each_event.delete()
    return HttpResponseRedirect("/dashboard")
