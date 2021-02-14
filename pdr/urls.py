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

urlpatterns = [
    path('', admin.site.urls),
    path('api/db/config', views.db_config),
    path('api/db/<slug:dbIdOrHandle>/tables', views.db_tables),
    path('api/broadcaster/<slug:btID>/fields', views.table_fields)
]
