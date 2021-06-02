
<!-- PROJECT LOGO -->
<br />
<p align="center">
<!--<a href="https://github.com/meena-erian/pdr">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>-->

  <h3 align="center">PDR (Pantograph Database Replicator)</h3>

  <p align="center">
    Flexible Database replication system compatible with most SQL databases
    <br />
    <!--
    <a href=""><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="">View Demo</a>
    ·
    <a href="/issues">Report Bug</a>
    ·
    <a href="/issues">Request Feature</a>
    -->
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#features">Features</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#quick-start">Quick Start</a>
      <!--
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
      -->
    </li>
    <!--<li><a href="#usage">Usage</a></li>-->
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

PDR is a standalone Django app for establishing a reliable, high-performance, cross-platform, live mirror of any table[s] in an SQL database server to any other SQL database server. 
<br />
Pantograph database replication is event driven, not time driven, ie. it doesn’t update the whole mirror database periodically; Instead, it updates each individual group of affected records in the affected table in the mirror at the moment it's modified in the original database. Which results in a more speedy instant update, yet consumes less bandwidth and server resources.
Pantograph database replication is also perfectly reliable because the server listening for changes doesn’t has to be online at the moment changes occur. Instead, the host server creates notification channels where changes are stacked awaiting the listening server’s action to read notification, and update its replications in remote servers.
<br />
A list of commonly used resources that I find helpful are listed in the acknowledgements.

### Features

1. Can replicate data to multiple tables in separate databases.
2. Can replicate data into a new structure, yet, keep it live.
3. Can replicate data from any kind of SQL database.
4. Very reliable as pdr events are created by native SQL trigger functions inside source databases.
5. High in performance as it’s event-driven.
6. One-way data replication can be used to join data from multiple different tables in multiple different databases into one live table.
7. Provides a simple easy to use GUI to configure replications.
8. Distributed as a standalone Django app wrapped in a PyPi package so you can easily integrate it with any existing Django Project.


### Built With

The project is based on Django, the popular python framework, SQLAlchemy, A wonderful open-source SQL abstraction layer for the Python programing language, and native SQL trigger functions.


## Quick start

1. Run  `pip install django-pdr` to install Pantograph Database Replicator's python package from the python package index

2. Add "django_pdr" and "django_ace" to your INSTALLED_APPS setting like this:

```python
INSTALLED_APPS = [
    ...
    'django_ace',
    'django_pdr',
]
```

3. Include the admin URLs anywhere in your project urls.py like this:

```python
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
]
```

1. Run `python manage.py migrate` to create django_pdr's data models.

2. Start the development server and visit http://127.0.0.1:8000/admin/
   to setup Databases, SourceTables and then Reflections.

3. In another terminal window, run the command `python manage.py pdr-reflect -i 1` to start the PDR background activity

<!-- GETTING STARTED -->
<!--
## Getting Started

In order to install and use Pantograph Database Replicator, first you have to determine a server that can access all source and destination databases. As you will install Pantograph databasae replicator on that server, or if you only want to try it, you can just create multiple SQLite files to use them as your example databases.


### Prerequisites

Pantograph Database Replicator requires that you have Python 3 and pip installed, in addition to the following python modules.


* Django python framework
  ```sh
  pip install django
  ```
* JavaScript based code-editor for Django
  ```sh
  pip install django-ace
  ```
* PostgreSQL database adapter
  ```sh
  pip install psycopg2
  ```
* For accurate timezone calculations
  ```sh
  pip install pytz
  ```
* SQL abstraction layer
  ```sh
  pip install SQLAlchemy
  ```
* For credentials encryption
  ```sh
  pip install django-pgcrypto
  ```

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/meena-erian/pdr.git
   ```
2. Open a terminal in the cloned folder
   ```sh
   cd pdr
   ```
3. Create Pantograph Database Replicator's database
   ```sh
   python manage.py migrate
   ```
4. Collect static files
   ```sh
   python manage.py collectstatic
   ```
5. Set up superuser's login
   ```sh
   python manage.py createsuperuser
   ```
6. Run the server
   ```sh
   python manage.py runserver
   ```
7. In order to install the server permanently as an Apache service, (which would also alow you to run it over SSL) see ["How to use Django with Apache and mod_wsgi”](https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/modwsgi/)



<!-- USAGE EXAMPLES 
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_
-->


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/meena-erian/pdr/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the Apache 2 License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Meena (Menas) Erian - menas@portacode.com

Project Link: [https://github.com/meena-erian/pdr](https://github.com/meena-erian/pdr)



<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [Python](https://www.python.org/)
* [Django](https://www.djangoproject.com/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Django ACE](https://github.com/django-ace/django-ace)
* [psycopg2](https://www.psycopg.org/docs/install.html)
* [pytz](https://pypi.org/project/pytz/)
* [Django pgcrypto](https://pypi.org/project/django-pgcrypto/)

