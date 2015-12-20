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
from django.conf.urls import include, url
from django.contrib import admin
from .views import *

urlpatterns = [
    url(r'^', get_calendar_data, name="get_calendar_data"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth/', index, name="oauthview"),                                   #Ability validate Oauth steps
    url(r'^oauth2callback', auth_return, name="auth_return"),                   #Ability validate Oauth steps
    url(r'^get_cal', get_calendar_data, name="get_calendar_data"),              #Ability to actually view the users calendar data for the tool (will port this to control panel)
    url(r'^unauthorize', unauthorize_account, name="unauthorize_account"),      #Ability to remove OAUTH token from DB for the current authenticated user
    url(r'^sync', pull_user_event_data, name="pull_user_event_data"),
    url(r'^create_event', create_event, name="create_event"),
    url(r'^delete_event', delete_event, name="delete_event"),
    url(r'^update_event', update_event, name="update_event")
]
