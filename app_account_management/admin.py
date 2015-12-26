from django.contrib import admin
from .models import UserExtended as UserExtended

class UserExtendedAdmin(admin.ModelAdmin):
  list_display = ['authenticated_user', 'dob', 'google_auth', 'google_initial_sync']

admin.site.register(UserExtended, UserExtendedAdmin)
