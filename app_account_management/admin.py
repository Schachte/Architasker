from django.contrib import admin
from .models import UserExtended as UserExtended

class UserExtendedAdmin(admin.ModelAdmin):
  list_display = ['authenticated_user', 'google_auth']

admin.site.register(UserExtended, UserExtendedAdmin)
