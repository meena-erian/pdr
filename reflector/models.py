from django.db import models
import json

# Create your models here.

class datasources:
    touple = (
        (0, "POSTGRESQL"),
        (1, "MSSQL"),
        (2, "MYSQL")
    )
    POSTGRESQL  = 0
    MSSQL       = 1
    MYSQL       = 2
    __list__ = [
        {
            "name" : "POSTGRESQL",
            "config" : {
                "dbname": "databasename",
                "user": "username",
                "password": "password",
                "host": "hostname or IP address",
                "port": 5432
            }
        },
        {
            "name" : "MSSQL",
            "config" : {
                "dbname": "databasename",
                "user": "username",
                "password": "password",
                "host": "hostname or IP address",
                "port": 1433
            }
        },
        {
            "name" : "MYSQL",
            "config" : {
                "dbname": "databasename",
                "user": "username",
                "password": "password",
                "host": "hostname or IP address",
                "port": 3306
            }
        }
    ]
    @classmethod
    def config(self, sourceid):
        return self.__list__[sourceid]["config"]
    @classmethod
    def json(self, sourceid):
        return json.dumps(self.__list__[sourceid]["config"], indent=2)


class Database(models.Model):
    handle = models.SlugField(max_length=200, help_text='Set a unique name for this database')
    source = models.IntegerField(choices=datasources.touple, help_text='Select what kind of SQL database this is')
    config = models.CharField(max_length=1000, help_text='Set connection information and credentials')
    description = models.CharField(max_length=200, help_text='Describe what this database is all about')
    connection_verified = models.BooleanField(default=False)
    def __str__(self):
        return self.handle