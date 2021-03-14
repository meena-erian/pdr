#from django.shortcuts import render
from django.http import HttpResponse
from .models import Database, BroadcastingTable, Reflection
import json
from django.contrib.admin.views.decorators import staff_member_required


# Create your views here.
@staff_member_required
def db_config(request):
    return  HttpResponse(json.dumps(Database.configs(), indent = 2), content_type="application/json")

@staff_member_required
def db_tables(request, dbIdOrHandle):
    try:
        if dbIdOrHandle.isnumeric():
            return HttpResponse(json.dumps(Database.objects.get(pk=dbIdOrHandle).tables(), indent = 2), content_type="application/json")
        return  HttpResponse(json.dumps(Database.objects.get(handle=dbIdOrHandle).tables(), indent = 2), content_type="application/json")
    except:
        return HttpResponse(json.dumps([]), content_type="application/json")

@staff_member_required
def table_fields(request, btID):
    try:
        bt = BroadcastingTable.objects.get(pk=btID)
    except:
        return HttpResponse(json.dumps([]), content_type="application/json")
    ret = bt.get_structure()
    return HttpResponse(json.dumps(ret, indent = 2), content_type="application/json") 

try:
    for reflection in Reflection.objects.all():
        reflection.refresh()
except Exception as e:
    print('Error starting reflections:', e)