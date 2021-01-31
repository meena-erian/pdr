from django.db import models
from django.core.exceptions import ValidationError
from sqlalchemy import create_engine, inspect
import urllib.parse
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
            "dialect" : "postgresql",
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
            "dialect" : "mssql+pymssql",
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
    def config(self, sourceid = -1):
        if sourceid == -1:
            return self.__list__
        return self.__list__[sourceid]["config"]
    @classmethod
    def json(self, sourceid = -1):
        if sourceid == -1:
            return json.dumps(self.__list__, indent=2)
        return json.dumps(self.__list__[sourceid]["config"], indent=2)


class Database(models.Model):
    handle = models.SlugField(max_length=200, help_text='Set a unique name for this database')
    source = models.IntegerField(choices=datasources.touple, help_text='Select what kind of SQL database this is')
    config = models.CharField(max_length=1000, help_text='Set connection information and credentials')
    description = models.CharField(max_length=200, help_text='Describe what this database is all about')
    def __str__(self):
        return self.handle
    def defaults(self):
        return datasources.config()
    def mount(self):
        config = json.loads(self.config)
        connectionStr = datasources.__list__[self.source]['dialect'] + '://'
        connectionStr += urllib.parse.quote_plus(config['user']) + ":" + urllib.parse.quote_plus(config['password']) + "@"
        connectionStr += config['host']
        if "port" in config:
            connectionStr += ":"
            connectionStr += str(config["port"])
        connectionStr += "/" + config["dbname"]
        return create_engine(connectionStr, echo = False)
    def tables(self):
        from .methods import make_query
        engine = self.mount().connect()
        results = []
        ret = engine.execute(make_query('list_tables'))
        for record in ret:
            results.append(record[0])
        return results
    def clean(self):
        try:
            self.mount().connect()
        except Exception as e:
            raise ValidationError('Failed to connect to database: {0}'.format(e))

class BroadcastingTable(models.Model):
    source_database = models.ForeignKey(Database, on_delete=models.CASCADE)
    source_table = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    fk_name = models.CharField(max_length=500, blank=True, null=True)
    def __str__(self):
        return self.source_database.handle + '.' + self.source_table
    def clean(self):
        if not hasattr(self, 'source_database'):
            raise ValidationError('Please select source database')
        if not hasattr(self, 'source_table') or len(self.source_table) < 3:
            raise ValidationError('Please select source table')
        ### Check if selected table exists in selected database. if not raise ValidationError
        db = self.source_database.mount()
        dbInfo = inspect(db)
        schema, table = self.source_table.split('.')
        try:
            tableInfo = dbInfo.get_columns(table, schema)
        except Exception as e:
            raise ValidationError('Table not found: {0}'.format(e))
        if len(tableInfo) < 1:
            raise ValidationError('Table not found')
        ### Install event listeners to the table
    def delete(self):
        ### try to remove event listeners from the databases table. If failed, raise ValidationError
        super(BroadcastingTable, self).delete()
