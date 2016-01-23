import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
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
            due_date = request.POST.get('task_due_date'),
            percent_to_complete = int(request.POST.get('task_percent')),
            estimated_time = float(request.POST.get('task_time')),
            difficulty = int(request.POST.get('task_priority')),
            # color = request.POST.get('color'),
            url = request.POST.get('task_url'),
            location = request.POST.get('task_location'),
            comments = request.POST.get('task_comments'),
            day_date = request.POST.get('task_day_date'),
            day_num = int(request.POST.get('task_day_num')),
        )

        if(int(request.POST.get('task_day_num')) == 0):
        	temp_model.day_num = 7

        if(request.POST.get('task_continuous') == "true"):
        	temp_model.continuous = True

        if(request.POST.get('task_pomodoro') == "true"):
        	temp_model.pomodoro = True

        temp_model.save()
        print("created task")
        return HttpResponse("none")


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Calculate overall priority and percentile for each task
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def prioritize_and_cluster(request):

	current_user = User.objects.get(username=request.user.username)
	user_tasks = Task.objects.filter(authenticated_user=current_user)

	'''
	Calculate and Store Priority
	'''

	for task in user_tasks:
		priority = task.estimated_time / (task.day_num - datetime.datetime.today().weekday()) + task.difficulty
		print(task.task_name + " " + str(priority))
		#Check output of current day tomorrow
		print("Current Day: " + str(datetime.datetime.today().weekday()))
		task.priority = priority
		task.save()

	'''
	Calculate and Store Percentile
	'''

	equation_N = user_tasks.count()

	for task in user_tasks:

		equation_L = Task.objects.filter(authenticated_user=current_user, priority__lt=task.priority).count()
		equation_S = Task.objects.filter(authenticated_user=current_user, priority=task.priority).count()
		
		pr_percent = ((equation_L + (0.5*equation_S)) / equation_N)*100
		print(task.task_name + " " + str(pr_percent))

		task.percentile = pr_percent
		task.save()

	return HttpResponse("The user has been queried successfully!")






