from django.contrib import admin
from .models import *
# Register your models here.

class UserEventAdmin(admin.ModelAdmin):

  list_display = ['authenticated_user', 'task_name', 'start_time', 'end_time',]


admin.site.register(UserEvent,UserEventAdmin)
