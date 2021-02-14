#from django.shortcuts import render
from django.http import HttpResponse
from .models import Database, BroadcastingTable
import json
from django.contrib.admin.views.decorators import staff_member_required


# Create your views here.
@staff_member_required
def db_config(request):
    return  HttpResponse(json.dumps(Database.defaults(Database), indent = 2), content_type="application/json")

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
    table_args = bt.source_table.split('.')
    table_args.reverse()
    table = bt.source_database.get_table(*table_args)
    ret = {"columns": {}}
    for column in table.columns:
        if hasattr(column, 'type'):
            c_type = column.type.__str__()
        else:
            c_type = None
        ret['columns'][column.name] = c_type
    ret['key'] = table.primary_key.columns.values()[0].name
    return HttpResponse(json.dumps(ret, indent = 2), content_type="application/json") 