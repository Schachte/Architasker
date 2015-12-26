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
from .views import *
from jet import *

urlpatterns = [
    url(r'^$', home, name="home"),                                              #Index loader
    url(r'^jet/', include('jet.urls', 'jet')),
    url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
    url(r'^admin/', include(admin.site.urls)),                                  #Admin login page
    url(r'^oauth/', index, name="oauthview"),                                   #Ability validate Oauth steps
    url(r'^oauth2callback', auth_return, name="auth_return"),                   #Ability validate Oauth steps
    url(r'^get_cal', get_calendar_data, name="get_calendar_data"),              #Ability to actually view the users calendar data for the tool (will port this to control panel)
    url(r'^unauthorize', unauthorize_account, name="unauthorize_account"),      #Ability to remove OAUTH token from DB for the current authenticated user
    url(r'^sync', pull_user_event_data, name="pull_user_event_data"),           #Grab all the data from Google
    url(r'^create_event/', create_event, name="create_event"),                  #Create event task AJAX URl
    url(r'^delete_event/', delete_event, name="delete_event"),                  #Delete event task AJAX URl
    url(r'^update_event/', update_event, name="update_event"),                  #Update event task AJAX URl
    url(r'^login', login_render, name="login_render"),                          #Login template render page
    url(r'^logmein', processor_login, name="processor_login"),                  #Background process to process the server request to authenticate user
    url(r'^logout', logout_process, name="logout_process")                      #Logout the requested user session
]
