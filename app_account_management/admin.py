from django.contrib import admin
from .models import UserExtended as UserExtended

class UserExtendedAdmin(admin.ModelAdmin):
  list_display = ['authenticated_user', 'google_auth', 'user_login_count']

admin.site.register(UserExtended, UserExtendedAdmin)
