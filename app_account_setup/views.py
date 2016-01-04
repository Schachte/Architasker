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

    #What loads in the select box onload
    time_zone_select_text = 'Select Your Timezone'

    #Returning data for google acct authentication
    if (current_user_extension.google_auth == False):
        google_is_auth = False
    else:
        google_is_auth = True


    if (current_user_extension.time_zone == 'None'):
        pass
    else:
        time_zone_select_text = current_user_extension.time_zone

    context = {

        'google_is_auth' : google_is_auth,
        'time_zone_select_text' : time_zone_select_text
    }

    return render(request, 'SETUP_SCREEN_PAGE/form.html', context)


def ajax_user_timezone(request):
    if request.method == "POST":

        #Submit the user timezone here
        sent_timezone = request.POST.get('user_tz')
        current_user = User.objects.get(username=request.user.username)
        current_user_extended = UserExtended.objects.get(authenticated_user=current_user)
        current_user_extended.time_zone = sent_timezone
        current_user_extended.save()

        return HttpResponse("success")
    else:
        return HttpResponse("failure")


def get_setup_module_post_data(request):
    if request.method == "POST":
        if 'wakeup' in request.POST:
            if not request.POST.get('wakeup') == 'Wake Up Time':
                pass
                # print(request.POST.get('wakeup'))
            else:
                return HttpResponse("Invalid wakeup time")

        if 'bedtime' in request.POST:
            if not request.POST.get('bedtime') == 'Sleepy Time':
                pass
            else:
                return HttpResponse("Invalid bed time")

        current_user = User.objects.get(username = request.user.username)
        current_user_extension = UserExtended.objects.get(authenticated_user=current_user)
        current_user_extension.initial_setup_complete = True
        current_user_extension.wakeup_time = request.POST.get('wakeup')
        current_user_extension.sleepy_time = request.POST.get('bedtime')
        current_user_extension.save()

        return HttpResponseRedirect("/setup_redirector")
    else:
        return HttpResponse("FAILURE!")


def setup_redirector(request):
    return render(request, 'SETUP_SCREEN_PAGE/redirector.html')
