from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from app_account_management.models import UserExtended
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

@login_required(login_url='/login')
def settings_loader(request):
    current_user = User.objects.get(username=request.user.username)
    current_user_ext = UserExtended.objects.get(authenticated_user=current_user)
    context = {

        'time_zone' : current_user_ext.time_zone,
    }

    return render(request, 'SETTINGS_PAGE/index.html', context)

@login_required(login_url='/login')
def processor_settings_name(request):
    if request.method == "POST":
        current_user = User.objects.get(username=request.user.username)
        if current_user.is_active:
            if 'first_name' in request.POST:
                if request.POST.get('first_name') != '':
                    current_user.first_name = request.POST.get('first_name')
                    current_user.save()
                    #print(current_user.first_name)
            if 'last_name' in request.POST:
                if request.POST.get('last_name') != '':
                    current_user.last_name = request.POST.get('last_name')
                    current_user.save()
                    #print(current_user.last_name)
            str = "hi"
            return str
    else:
        return HttpResponse("Not a POST submission")

@login_required(login_url='/login')
def processor_settings_email(request):
    if request.method == "POST":
        current_user = User.objects.get(username=request.user.username)
        if current_user.is_active:
            if 'email' in request.POST:
                if request.POST.get('email') != '':
                    #print(current_user.email)
                    current_user.email = request.POST.get('email')
                    current_user.save()
                    #print(current_user.email)
            return HttpResponse("none")
    else:
        return HttpResponse("Not a POST submission")

@login_required(login_url='/login')
def processor_settings_tz(request):
    if request.method == "POST":
        current_user = User.objects.get(username=request.user.username)
        current_user_ext = UserExtended.objects.get(authenticated_user=current_user)
        if current_user.is_active:
            if 'tz' in request.POST:
                if request.POST.get('tz') != '':
                    print(current_user_ext.time_zone)
                    current_user_ext.time_zone = request.POST.get('tz')
                    current_user_ext.save()
                    print(current_user_ext.time_zone)
        return HttpResponse("none")
    else:
        return HttpResponse("Not a POST submission")

@login_required(login_url='/login')
def processor_settings_password(request):
    if request.method == "POST":
        current_user = User.objects.get(username=request.user.username)
        if current_user.is_active:
            if 'old_pass' in request.POST:
                oldpass = request.POST.get('old_pass')
                if oldpass == '':
                    return HttpResponse("Old password missing")
                else:
                    if current_user.check_password(oldpass):
                        if 'new_pass' in request.POST:  
                            newpass = request.POST.get('new_pass')
                            if newpass == '':
                                return HttpResponse("new password missing")
                            else:
                                newpass2 = request.POST.get('new_pass2')
                                if newpass == '':
                                    return HttpResponse("new password missing")
                                else:
                                    if (not str(newpass) == str(newpass2)):
                                        return HttpResponse("Passwords do not match") 
                                    else:
                                        current_user.set_password(newpass) 
                                        current_user.save()

                                        user = authenticate(username=current_user.username, password=newpass)
                                        login(request, user)
                    else:
                        return HttpResponse("Old password does not match")
        return HttpResponse("none")
    else:
        return HttpResponse("Not a POST submission")