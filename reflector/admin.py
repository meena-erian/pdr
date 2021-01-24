from django.contrib import admin
from django import forms
from .models import Database
from django_ace import AceWidget

# Register your models here.

class DatabaseForm(forms.ModelForm):
    class Meta:
        model = Database
        widgets = {
            'config': AceWidget(mode='json')
        }
        fields = ['handle', 'description', 'config']

class DatabaseAdmin(admin.ModelAdmin):
    form = DatabaseForm
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