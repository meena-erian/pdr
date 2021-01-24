from django.contrib import admin
from .models import Database

# Register your models here.

class DatabaseAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs['exclude'] = ['connection_verified']
        return super(DatabaseAdmin, self).get_form(request, obj, **kwargs)
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['source']
        else:
            return []

admin.site.register(Database, DatabaseAdmin)