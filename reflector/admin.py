from django.contrib import admin
from .models import Database

# Register your models here.

class DatabaseAdmin(admin.ModelAdmin):
    None

admin.site.register(Database, DatabaseAdmin)