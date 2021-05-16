"""pdr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from reflector import views

admin.site.site_header = "Pantograph Database Replicator Admin"
admin.site.site_title = "PDR Admin Portal"
admin.site.index_title = "Welcome to Pantograph Database Replicator Portal"

urlpatterns = [
    # Set Admin side on the home page.
    path('', admin.site.urls),
    # An api that returns a list of default database configurations.
    path('api/db/config', views.db_config),
    # An api that takes the id or the slug of a database and
    # returns a list of all tables in that database.
    path('api/db/<slug:dbIdOrHandle>/tables', views.db_tables),
    # An api that takes the id or slug of a sourec table and
    # returns the structure of that table.
    path('api/source/<slug:btID>/fields', views.table_fields)
]
