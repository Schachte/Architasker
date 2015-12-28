from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect

# Create your views here.
#def dash_loader(request):
#    return render(request, 'DASHBOARD_PAGE/index.html')

def settings_loader(request):
	return render(request, 'SETTINGS_PAGE/index.html')

def processor_settings(request):
    #Not sure this is a secure way of going about this....
    if user is not None:
        if user.is_active:
            login(request, user)
            UE_model = UserExtended.objects.get(authenticated_user=user)

    if request.method == "POST":
        if 'time_zone' in request.POST:
            if request.POST.get('time_zone') != '':
            	print('random stuff')
        if 'first_name' in request.POST:
            if request.POST.get('first_name') != '':
               print('random stuff') 
        if 'last_name' in request.POST:
            if request.POST.get('last_name') != '':
                print('random stuff')
       	if 'pass_word' in request.POST:
            if request.POST.get('pass_word') != '':
				print('random stuff')
        if 'user_email' in request.POST:
            if request.POST.get('user_email') != '':
                print('random stuff')
        if (not str(request.POST.get('pass_word')) == str(request.POST.get('pass_word2'))):
            return HttpResponse("Passwords do not match")

        new_user = User.objects.create(

            username = request.POST.get('user_name'),
            first_name = request.POST.get('first_name'),
            last_name = request.POST.get('last_name'),
            email = request.POST.get('user_email'),
        )
        new_user.set_password(request.POST.get('pass_word'))
        new_user.save()

        new_user_extended = UserExtended.objects.create(
            authenticated_user = new_user
        )
        new_user_extended.save()

        return HttpResponse("Account created successfully, please login.")
    else:
        return HttpResponse("Error")
