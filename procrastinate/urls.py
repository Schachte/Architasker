"""procrastinate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

'''
Load the necessary functions from the APP views files.
'''
from django.conf.urls import include, url
from django.contrib import admin
from app_account_management.views import login_process as processor_login
from app_account_management.views import login_view as login_render
from app_account_management.views import *
from app_dashboard.views import *
from app_account_setup.views import *
from app_calendar.views import *
from app_task_redistribution.views import *
from app_tasks.views import *
from .views import *
from jet import *


urlpatterns = [
    url(r'^$', home, name="home"),                                              #Index loader
    url(r'^/$', home, name="home"),
    url(r'^jet/', include('jet.urls', 'jet')),
    url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
    url(r'^admin/', include(admin.site.urls)),                                  #Admin login page
    url(r'^oauth/', 'app_calendar.views.index', name="oauthview"),                                   #Ability validate Oauth steps
    url(r'^oauth2callback', 'app_calendar.views.auth_return', name="auth_return"),                   #Ability validate Oauth steps
    url(r'^unauthorize', 'app_calendar.views.unauthorize_account', name="unauthorize_account"),      #Ability to remove OAUTH token from DB for the current authenticated user
    url(r'^sync', 'app_calendar.views.pull_user_event_data', name="pull_user_event_data"),           #Grab all the data from Google
    url(r'^create_event/', 'app_calendar.views.create_event', name="create_event"),                  #Create event task AJAX URl
    url(r'^delete_event/', 'app_calendar.views.delete_event', name="delete_event"),                  #Delete event task AJAX URl
    url(r'^update_event/', 'app_calendar.views.update_event', name="update_event"),                  #Update event task AJAX URl
    url(r'^create_task/', 'app_tasks.views.create_task', name="create_task"),
    url(r'^prioritize_and_cluster/', 'app_task_redistribution.views.prioritize_and_cluster', name="prioritize_and_cluster"),
    url(r'^task_per_day/', 'app_task_redistribution.views.task_hours_per_day', name="task_hours_per_day"), #remove after testing
    url(r'^login', login_render, name="login_render"),                          #Login template render page
    url(r'^register$', register_view, name="register_view"),
    url(r'^registermein', processor_register, name="processor_register"),
    url(r'^logmein', processor_login, name="processor_login"),                  #Background process to process the server request to authenticate user
    url(r'^logout', logout_process, name="logout_process"),                      #Logout the requested user session
    url(r'^dashboard', 'app_calendar.views.get_calendar_data', name="get_calendar_data"),
    url(r'^settingsavename', processor_settings_name, name="processor_settings_name"),
    url(r'^settingsaveemail', processor_settings_email, name="processor_settings_email"),
    url(r'^settingsavetz', processor_settings_tz, name="processor_settings_tz"),
    url(r'^settingsavepassword', processor_settings_password, name="processor_settings_password"),
    url(r'^settings', settings_loader, name="settings_loader"),
    url(r'^setup$', screen_setup_module, name='screen_setup_module'),
    url(r'^setup_processor$', get_setup_module_post_data, name='get_setup_module_post_data'), #Process the POST data that is submitted by the fomr for the user
    url(r'^setup_redirector$', setup_redirector, name='setup_redirector'),
    url(r'^persist_timezone_ajax', ajax_user_timezone, name='ajax_user_timezone'),
    url(r'^clear_google_tasks', clear_google_tasks, name='clear_google_tasks'),
    url(r'^archicalc', task_distribution, name='task_distribution'),
    url(r'^get_distance', get_travel_time, name='get_travel_time'),
    url(r'^allocate_test', allocate_tasks, name='allocate_tasks')


]

admin.site.site_header = 'Architasker'
