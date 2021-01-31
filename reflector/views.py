from django.shortcuts import render
from django.http import HttpResponse
from .models import Database
import json
from django.contrib.admin.views.decorators import staff_member_required


# Create your views here.
@staff_member_required
def connection_config(request):
    return  HttpResponse(json.dumps(Database.defaults(Database), indent = 2), content_type="application/json")

@staff_member_required
def connection_tables(request, connectionIdOrHandle):
    try:
        if connectionIdOrHandle.isnumeric():
            return HttpResponse(json.dumps(Database.objects.get(pk=connectionIdOrHandle).tables(), indent = 2), content_type="application/json")
        return  HttpResponse(json.dumps(Database.objects.get(handle=connectionIdOrHandle).tables(), indent = 2), content_type="application/json")
    except:
        return HttpResponse(json.dumps([]), content_type="application/json")
