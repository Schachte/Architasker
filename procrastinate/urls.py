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
from account_management.views import login_process as processor_login
from account_management.views import login_view as login_render
from account_management.views import *
from .views import *


urlpatterns = [

    url(r'^$', home, name="home"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth/', 'app_calendar.views.index', name="oauthview"),                                   #Ability validate Oauth steps
    url(r'^oauth2callback', 'app_calendar.views.auth_return', name="auth_return"),                   #Ability validate Oauth steps
    url(r'^get_cal', 'app_calendar.views.get_calendar_data', name="get_calendar_data"),              #Ability to actually view the users calendar data for the tool (will port this to control panel)
    url(r'^unauthorize', 'app_calendar.views.unauthorize_account', name="unauthorize_account"),      #Ability to remove OAUTH token from DB for the current authenticated user
    url(r'^sync', 'app_calendar.views.pull_user_event_data', name="pull_user_event_data"),
    url(r'^create_event/', 'app_calendar.views.create_event', name="create_event"),
    url(r'^delete_event/', 'app_calendar.views.delete_event', name="delete_event"),
    url(r'^update_event/', 'app_calendar.views.update_event', name="update_event"),
    url(r'^login', login_render, name="login_render"),
    url(r'^logmein', processor_login, name="processor_login"),
    url(r'^logout', logout_process, name="logout_process"),
    url(r'^tester', tester_login_form, name="tester_login_form"),

]
