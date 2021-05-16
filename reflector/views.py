# from django.shortcuts import render
from django.http import HttpResponse
from .models import Database, SourceTable, Reflection
import json
from django.contrib.admin.views.decorators import staff_member_required
import logging


@staff_member_required
def db_config(request):
    """A function used to create a REASTful API to listing default
    configurations for each RDBMS type"""
    return HttpResponse(json.dumps(
        Database.configs(), indent=2), content_type="application/json")


@staff_member_required
def db_tables(request, dbIdOrHandle):
    """A function used to list all tables in a specific database"""
    try:
        if dbIdOrHandle.isnumeric():
            return HttpResponse(json.dumps(Database.objects.get(
                pk=dbIdOrHandle).tables(), indent=2),
                content_type="application/json")
        return HttpResponse(json.dumps(Database.objects.get(
            handle=dbIdOrHandle).tables(), indent=2),
            content_type="application/json")
    except Exception as e:
        return HttpResponse(json.dumps([]), content_type="application/json")


@staff_member_required
def table_fields(request, btID):
    """A function used to retrive the structure of a source table"""
    try:
        bt = SourceTable.objects.get(pk=btID)
    except Exception as e:
        return HttpResponse(json.dumps([]), content_type="application/json")
    ret = bt.get_structure()
    return HttpResponse(json.dumps(
        ret, indent=2), content_type="application/json")


try:
    for reflection in Reflection.objects.all():
        reflection.refresh()
except Exception as e:
    logging.error('Cannot start reflections:{0}'.format(e))
