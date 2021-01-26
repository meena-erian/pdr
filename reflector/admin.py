from django.contrib import admin
from django import forms
from .models import Database, BroadcastingTable
from django_ace import AceWidget

# Register your models here.

class DatabaseForm(forms.ModelForm):
    class Meta:
        model = Database
        widgets = {
            'config': AceWidget(mode='json')
        }
        fields = ['handle', 'description', 'source', 'config']

class DatabaseAdmin(admin.ModelAdmin):
    form = DatabaseForm
    list_display = ['handle', 'description', 'source']
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['source']
        else:
            return []

class BroadcastingTableAdmin(admin.ModelAdmin):
    exclude = ['fk_name']
    list_display = []
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['source_database', 'source_table']
        else:
            return []

admin.site.register(Database, DatabaseAdmin)
admin.site.register(BroadcastingTable, BroadcastingTableAdmin)