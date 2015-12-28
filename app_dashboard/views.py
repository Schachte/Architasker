from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from app_account_management.models import UserExtended


def settings_loader(request):
	return render(request, 'SETTINGS_PAGE/index.html')

def processor_settings(request):
    if request.method == "POST":
        print("Method is post")
        current_user = User.objects.get(username=request.user.username)
        current_user_ext = UserExtended.objects.get(authenticated_user=current_user)
        if current_user.is_active:
            print("user is active")
        return HttpResponseRedirect("/settings/")
    else:
        return HttpResponse("Not a POST submission")
