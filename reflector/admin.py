from django.contrib import admin
from django import forms
from .models import Database, BroadcastingTable
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
            return ['source']
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
    list_display = []
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['source_database', 'source_table']
        else:
            return []

admin.site.register(Database, DatabaseAdmin)
admin.site.register(BroadcastingTable, BroadcastingTableAdmin)