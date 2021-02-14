from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from sqlalchemy import *
import urllib.parse
import json

# Create your models here.
pdr_prefix = 'pdr_event'

class datasources:
    touple = (
        (0, "PostgreSQL"),
        (1, "Microsoft SQL"),
        (2, "MySQL/MariaDB"),
        (3, "SQLite"),
        (4, "FireBird")
    )
    POSTGRESQL  = 0
    MSSQL       = 1
    MYSQL       = 2
    SQLIGHT     = 3
    FIREBIRD    = 4
    __list__ = [
        {
            "name" : "PostgreSQL",
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
            "name" : "Microsoft SQL",
            "dialect" : "mssql+pymssql",
            "config" : {
                "dbname": "master",
                "user": "sa",
                "password": "",
                "host": "localhost",
                "port": 1433
            }
        },
        {
            "name" : "MySQL",
            "dialect" : "mysql+mysqldb",
            "config" : {
                "dbname": "master",
                "user": "root",
                "password": "password",
                "host": "localhost",
                "port": 3306
            }
        },
        {
            "name" : "SQLite",
            "dialect" : "sqlite+pysqlite",
            "config" : {
                "dbfile" : "path/to/database.db"
            }
        },
        {
            "name" : "FireBird",
            "dialect" : "firebird+kinterbasdb",
            "config" : {
                "dbname": "databasename",
                "user": "SYSDBA",
                "password": "masterkey",
                "host": "localhost",
                "path": "C:/projects/databases/myproject.fdb",
                "port": 3050
            }
        },
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
    def mount(self):
        config = json.loads(self.config)
        connectionStr = datasources.__list__[self.source]['dialect'] + '://'
        if 'dbfile' in config:
            connectionStr += '/' + config['dbfile']
        else:
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
        if self.source == datasources.SQLIGHT:
            ret = engine.execute(make_query(datasources.__list__[self.source]['dialect'] + '/list_tables'))
        else:
            ret = engine.execute(make_query('list_tables'))
        for record in ret:
            results.append(record[0])
        return results
    def meta(self, schema = None):
        db = self.mount()
        return MetaData(bind=db, reflect=True, schema=schema)
    def get_table(self, table, schema = None):
        meta = self.meta(schema)
        if schema != None:
            table = schema + '.' + table
        return meta.tables[table]
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
        from .methods import exec_query
        if not hasattr(self, 'source_database'):
            raise ValidationError('Please select source database')
        if not hasattr(self, 'source_table') or len(self.source_table) < 3:
            raise ValidationError('Please select source table')
        ### Check if selected table exists in selected database. if not raise ValidationError
        db = self.source_database.mount()
        table_path = self.source_table.split('.')
        if len(table_path) == 1:
            schema = None
            table = table_path[0]
        elif len(table_path) == 2:
            schema, table = table_path
        else:
            raise ValidationError('Invalid table path')
        try:
            table_obj = Table(table, MetaData(), autoload=True, autoload_with=db, schema=schema)
        except Exception as e:
            raise ValidationError('Table not found: {0}'.format(e))
        primaryKey = table_obj.primary_key.columns.values()[0]
        pdr_table_name = '{0}_o_{1}_o_{2}'.format(pdr_prefix, schema, table)
        meta = MetaData()
        pdr_event = Table(
            pdr_table_name, meta,
            Column('id', Integer, primary_key = True, autoincrement = True),
            Column('c_action', String(6)),
            Column('c_record', primaryKey.type),
            Column('c_time', DateTime, default=datetime.utcnow)
        )
        meta.create_all(db)
        exec_query(
            db,
            datasources.__list__[self.source_database.source]['dialect'] + '/create_event_listener',
            pdr_prefix,
            schema,
            table,
            primaryKey.name
        )
    def delete(self):
        from .methods import exec_query
        table_path = self.source_table.split('.')
        if len(table_path) == 1:
            schema = None
            table = table_path[0]
        elif len(table_path) == 2:
            schema, table = table_path
        db = self.source_database.mount()
        ### try to remove event listeners from the databases table. If failed, raise ValidationError
        exec_query(
            db,
            datasources.__list__[self.source_database.source]['dialect'] + '/delete_event_listener',
            pdr_prefix,
            schema,
            table
        )
        super(BroadcastingTable, self).delete()

class Reflection(models.Model):
    description = models.CharField(max_length=500)
    source_table = models.ForeignKey(BroadcastingTable, on_delete=models.CASCADE)       # The source broadcasting table
    destination_database = models.ForeignKey(Database, on_delete=models.CASCADE)        # The destination datastorage
    destination_table = models.CharField(max_length=500)
    last_commit = models.IntegerField(help_text='id of last pdr_event executed', blank=True, null=True)
    source_fields = models.CharField(help_text='json representation of the structure of the source table (read only)', max_length=1000)
    record_reflection = models.CharField(help_text='json configuration that represents the translation from source data to destination structure', max_length=1000)
    def __str__(self):
        return '{0}-->{1}.{2} : {3}'.format(self.source_table,self.destination_database, self.destination_table, self.description)