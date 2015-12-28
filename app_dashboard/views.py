from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.models import User
from app_account_management.models import UserExtended

# Create your views here.
#def dash_loader(request):
#    return render(request, 'DASHBOARD_PAGE/index.html')

def settings_loader(request):
	return render(request, 'SETTINGS_PAGE/index.html')

def processor_settings(request):
    #Not sure this is a secure way of going about this....
    print('hello')
    if request.method == "POST":
        current_user = User.objects.get(username=request.user.username)
        current_user_ext = UserExtended.objects.get(authenticated_user=current_user)
        print('hello?')
        if current_user.is_active:
            login(request, user)
            print(current_user)
        if 'time_zone' in request.POST:
            if request.POST.get('time_zone') != '':
            	print(current_user_ext.time_zone)
        if 'first_name' in request.POST:
            if request.POST.get('first_name') != '':
                print(current_user.first_name) 
        if 'last_name' in request.POST:
            if request.POST.get('last_name') != '':
                print(current_user.last_name)
       	if 'pass_word' in request.POST:
            if request.POST.get('pass_word') != '':
				print('password')
        if 'user_email' in request.POST:
            if request.POST.get('user_email') != '':
                print(current_user.email)
        #if (not str(request.POST.get('pass_word')) == str(request.POST.get('pass_word2'))):
        #    return HttpResponse("Passwords do not match")

        #new_user.set_password(request.POST.get('pass_word'))
        #new_user.save()

        #return HttpResponse("A")
    else:
        return HttpResponse("Error")
    context = {}
    return render(request, 'SETTINGS_PAGE/index.html', context)