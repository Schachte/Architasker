from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect

# Create your views here.
def dash_loader(request):
    return render(request, 'DASHBOARD_PAGE/index.html')
