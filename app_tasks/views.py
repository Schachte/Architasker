from django.shortcuts import render

from django.contrib.auth.models import User
from procrastinate import settings
from .models import UserTask as Task

# Create your views here.

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Function to store new task into database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def create_task(request):
	
    if request.method == 'POST':
        current_user = User.objects.get(id=request.user.id)
        temp_model = Task.objects.create(
            authenticated_user = current_user,
            task_name = request.POST.get('task_name'),
            due_date = request.POST.get('task_date'),
            percent_to_complete = int(request.POST.get('task_percent')),
            estimated_time = float(request.POST.get('task_time')),
            priority = int(request.POST.get('task_priority')),
            # color = request.POST.get('color'),
            url = request.POST.get('task_url'),
            location = request.POST.get('task_location'),
            comments = request.POST.get('task_comments')
        )

        if(request.POST.get('task_continuous') == "true"):
        	temp_model.continuous = True

        if(request.POST.get('task_pomodoro') == "true"):
        	temp_model.pomodoro = True

        temp_model.save()
        print("created task")
        return HttpResponse("none")