from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from app_account_management.models import UserExtended

# Create your views here.
def screen_setup_module(request):
    current_user = User.objects.get(username=request.user.username)
    current_user_extension = UserExtended.objects.get(authenticated_user=current_user)

    #Google acct has been authenticated
    google_is_auth = False

    #Returning data for google acct authentication
    if (current_user_extension.google_auth == False):
        google_is_auth = False
    else:
        google_is_auth = True

    context = {

        'google_is_auth' : google_is_auth
    }

    return render(request, 'SETUP_SCREEN_PAGE/form.html', context)

def get_setup_module_post_data(request):
    if request.method == "POST":
        if 'wakeup' in request.POST:
            if not request.POST.get('wakeup') == 'Wake Up Time':
                print(request.POST.get('wakeup'))
            else:
                return HttpResponse("Invalid wakeup time")

        if 'bedtime' in request.POST:
            if not request.POST.get('bedtime') == 'Sleepy Time':
                print(request.POST.get('bedtime'))
            else:
                return HttpResponse("Invalid bed time")

        current_user = User.objects.get(username = request.user.username)
        current_user_extension = UserExtended.objects.get(authenticated_user=current_user)
        current_user_extension.initial_setup_complete = True
        current_user_extension.save()

        return HttpResponseRedirect("/setup_redirector")
    else:
        return HttpResponse("FAILURE!")


def setup_redirector(request):
    return render(request, 'SETUP_SCREEN_PAGE/redirector.html')
