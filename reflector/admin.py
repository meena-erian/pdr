from django.contrib import admin
from django import forms
from .models import Database, SourceTable, Reflection
from django_ace import AceWidget
from .methods import make_script

class DatabaseForm(forms.ModelForm):
    class Meta:
        model = Database
        widgets = {
            'config': AceWidget(mode='json')
        }
        fields = ['handle', 'description', 'source', 'config']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # once an RDBMS type is selected, run the JS code to show default JSON config for it
        self.fields['source'].widget.attrs.update({"onchange" : make_script('list_config')})

class DatabaseAdmin(admin.ModelAdmin):
    form = DatabaseForm
    list_display = ['handle', 'description', 'source']

class SourceTableForm(forms.ModelForm):
    class Meta:
        model = SourceTable
        fields = ['source_database', 'source_table', 'description']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'source_table' in self.fields:
            # disable the source table field until a source database is selected first
            self.fields['source_table'].widget.attrs.update({"disabled" : "disabled"})
        if 'source_database' in self.fields:
            # once a source database is selected, reenable the source table field show a list of existing tables
            self.fields['source_database'].widget.widget.attrs.update({"onchange" : make_script('list_db_tables')})

class SourceTableAdmin(admin.ModelAdmin):
    form = SourceTableForm
    list_display = ['__str__', 'description']
    ordering = ('source_database', 'source_table')

class ReflectionForm(forms.ModelForm):
    class Meta:
        model = Reflection
        widgets = {
            'destination_fields': AceWidget(mode='json'),
            'source_fields': AceWidget(mode='json', readonly=True),
            'reflection_statment': AceWidget(mode='sql')
        }
        fields = ('description', 'source_table', 'destination_database', 'destination_table', 'source_fields', 'destination_fields', 'reflection_statment', 'ignore_delete_events', 'active')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'destination_table' in self.fields:
            # Regenerate reflection configurations on the client side when destination table is changes by the user.
            self.fields['destination_table'].widget.attrs.update({"disabled" : "disabled", "onchange" : make_script('get-reflection-template', 'someid')})
        if 'destination_database' in self.fields:
            # list posible destination tables when the user selects the source database.
            self.fields['destination_database'].widget.widget.attrs.update({"onchange" : make_script('bind-connection-tables', 'id_destination_table')})
        if 'source_table' in self.fields:
            # Regenerate reflection configurations on the client side when source table is changes by the user.
            self.fields['source_table'].widget.widget.attrs.update({"onchange" : make_script('get-reflection-template', 'someid')})

class ReflectionAdmin(admin.ModelAdmin):
    exclude = ['last_commit']
    form = ReflectionForm
    list_display = ['__str__', 'last_commit', 'last_updated', 'ignore_delete_events', 'active']
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['source_table', 'destination_database', 'destination_table']
        else:
            return []

admin.site.register(Database, DatabaseAdmin)
admin.site.register(SourceTable, SourceTableAdmin)
admin.site.register(Reflection, ReflectionAdmin)