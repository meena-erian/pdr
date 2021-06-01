=====
reflector
=====

Reflector is a Django app to replicate sql tables.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "reflector" and "django_ace" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'django_ace',
        'reflector',
    ]

2. Include the admin URLs anywhere in your project urls.py like this::

    from django.contrib import admin

    path('admin/', admin.site.urls),

3. Run  ``python manage.py makemigrations``  and then 
    ``python manage.py migrate`` to create the reflector models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to setup Databases, SourceTables and then Reflections.