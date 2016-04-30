import datetime
import pytz
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.models import User
from procrastinate import settings
from .models import UserTask as Task
from app_account_management.models import UserExtended
from dateutil.parser import parse
from app_task_redistribution.views import allocate_tasks
from app_task_redistribution.views import task_conflict_analysis

import json
from django.core import serializers
# from django.utils import simplejson


# Create your views here.

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to store new task into database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def create_task(request):
	
    if request.method == 'POST':
    	print(request.POST.get('task_location'))
    	print(request.POST.get('task_transit_mode'))
        current_user = User.objects.get(id=request.user.id)
        temp_model = Task.objects.create(
            authenticated_user = current_user,
            task_name = request.POST.get('task_name'),
            due_date = request.POST.get('task_due_date'),
            percent_to_complete = float(request.POST.get('task_percent'))/100,
            estimated_time = float(request.POST.get('task_time')),
            difficulty = int(request.POST.get('task_priority')),
            # color = request.POST.get('color'),
            url = request.POST.get('task_url'),
            comments = request.POST.get('task_comments'),
            day_date = request.POST.get('task_day_date'),
            day_num = int(request.POST.get('task_day_num')),
            location = request.POST.get('task_location'),
            transit_mode = int(request.POST.get('task_transit_mode'))
        )

        if(int(request.POST.get('task_day_num')) == 0):
        	temp_model.day_num = 7

        if(request.POST.get('task_continuous') == "true"):
        	temp_model.continuous = True

        if(request.POST.get('task_pomodoro') == "true"):
        	temp_model.pomodoro = True

        temp_model.save()

        return_conflict_data = task_conflict_analysis(request, temp_model)

        ## return array with 0/1, free hours, and task hours
        if(return_conflict_data[0] == 1):
            temp_model.delete()
            print("CONFLICT")

            #taskname, available_hours, needed_available_hours
            try:

                json_list_return = json.dumps({'conflict_bool' : 1, 'task_name' : return_conflict_data[1], 'available_hours' : return_conflict_data[2], 'needed_available_hours' : return_conflict_data[3]})

            except Exception as e:
                print(e)

            print("created task")

            return HttpResponse(json_list_return)



            #RETURN NECESSARY INFO TO MODAL WINDOW

        else:
            allocate_tasks(request)

            json_list_return = json.dumps({'conflict_bool' : 0})

            return HttpResponse(json_list_return)









