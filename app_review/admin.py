from django.contrib import admin
from .models import *

# Register your models here.
class ReviewAdmin(admin.ModelAdmin):

  list_display = ['authenticated_user',]


admin.site.register(ReviewModel, ReviewAdmin)