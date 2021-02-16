from django.contrib import admin
from django import forms
from .models import Database, BroadcastingTable, Reflection
from django_ace import AceWidget
from .methods import make_script

# Register your models here.

class DatabaseForm(forms.ModelForm):
    class Meta:
        model = Database
        widgets = {
            'config': AceWidget(mode='json')
        }
        fields = ['handle', 'description', 'source', 'config']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source'].widget.attrs.update({"onchange" : make_script('list_config')})

class DatabaseAdmin(admin.ModelAdmin):
    form = DatabaseForm
    list_display = ['handle', 'description', 'source']
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [] #['source']
        else:
            return []

class BroadcastingTableForm(forms.ModelForm):
    class Meta:
        model = BroadcastingTable
        fields = ['source_database', 'source_table', 'description']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_table'].widget.attrs.update({"disabled" : "disabled"})
        self.fields['source_database'].widget.widget.attrs.update({"onchange" : make_script('list_db_tables')})

class BroadcastingTableAdmin(admin.ModelAdmin):
    form = BroadcastingTableForm
    exclude = ['fk_name']
    list_display = ['source_database', 'source_table', 'description']
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [] #['source_database', 'source_table']
        else:
            return []

class ReflectionForm(forms.ModelForm):
    class Meta:
        model = Reflection
        widgets = {
            'record_reflection': AceWidget(mode='json'),
            'source_fields': AceWidget(mode='json', readonly=True)
        }
        fields = ('description', 'source_table', 'destination_database', 'destination_table', 'source_fields', 'record_reflection')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'destination_table' in self.fields:
            self.fields['destination_table'].widget.attrs.update({"disabled" : "disabled", "onchange" : make_script('get-broadcasting-template', 'someid')})
        if 'destination_database' in self.fields:
            self.fields['destination_database'].widget.widget.attrs.update({"onchange" : make_script('bind-connection-tables', 'id_destination_table')})
        if 'source_table' in self.fields:
            self.fields['source_table'].widget.widget.attrs.update({"onchange" : make_script('get-broadcasting-template', 'someid')})

class ReflectionAdmin(admin.ModelAdmin):
    exclude = ['last_commit']
    form = ReflectionForm
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['source_table', 'destination_database', 'destination_table']
        else:
            return []

admin.site.register(Database, DatabaseAdmin)
admin.site.register(BroadcastingTable, BroadcastingTableAdmin)
admin.site.register(Reflection, ReflectionAdmin)