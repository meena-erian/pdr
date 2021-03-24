from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import *
import urllib.parse
import json
import threading
import pytz

# Create your models here.
pdr_prefix = 'pdr_event'
pdr_reflection_loops = {}
cached_database_metas = {}
database_engines = {}

def add_column(engine, table_name, column):
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    engine.execute('ALTER TABLE %s ADD COLUMN %s %s NULL' % (table_name, column_name, column_type))

def get_pk(table):
    from sqlalchemy.inspection import inspect
    ins = inspect(table)
    return ins.identity

def typeFullName(o):
  module = o.__class__.__module__
  if module is None or module == str.__class__.__module__:
    return o.__class__.__name__  # Avoid reporting __builtin__
  else:
    return module + '.' + o.__class__.__name__


def ColTypeToStr(Type):
    instanceClassName = typeFullName(Type)
    mainParent, path = instanceClassName.split('.', 1)
    if mainParent != 'sqlalchemy':
        raise Exception('Invalid type for SQL')
    if hasattr(Type, 'length') and Type.length != None:
        path += '({0})'.format(Type.length)
    return path

def StrToColType(TypePath):
    import sqlalchemy
    pathentries = TypePath.split('.')
    currentEntry = sqlalchemy
    for entry in pathentries:
        if '(' in entry:
            className, varLength = entry.split('(', 1)
            varLength = int(varLength.strip(' ()'))
            currentEntry = currentEntry.__dict__[className](varLength)
        else:
            currentEntry = currentEntry.__dict__[entry] 
    return currentEntry


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
    def configs():
        return datasources.__list__
    def mount(self):
        if str(self.pk) in database_engines:
            return database_engines[str(self.pk)]
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
        database_engines[str(self.pk)] = create_engine(connectionStr, echo = False)
        return database_engines[str(self.pk)]
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
        metaid = '{0}.{1}'.format(self.pk, schema)
        if metaid in cached_database_metas:
            return cached_database_metas[metaid]
        else:
            print('Loading meta data for {0} schema {1}'.format(self, schema))
            cached_database_metas[metaid] = MetaData(bind=db, reflect=True, schema=schema)
            return cached_database_metas[metaid]
    def get_table(self, table, schema = None):
        meta = self.meta(schema)
        if schema != None:
            table = schema + '.' + table
        if table in meta.tables:
            return meta.tables[table]
        else:
            return None
    def clean(self):
        try:
            self.mount().connect()
        except Exception as e:
            raise ValidationError('Failed to connect to database: {0}'.format(e))

class SourceTable(models.Model):
    source_database = models.ForeignKey(Database, on_delete=models.CASCADE)
    source_table = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    fk_name = models.CharField(max_length=500, blank=True, null=True)
    def get_table(self):
        path = self.source_table.split('.')
        path.reverse()
        return self.source_database.get_table(*path)
    def get_pdr_table(self):
        table_path = self.source_table.split('.')
        if len(table_path) == 1:
            table_path.insert(0, 'None')
        pdr_table_name = '{0}_o_{1}_o_{2}'.format(pdr_prefix, *table_path)
        return self.source_database.get_table(pdr_table_name)
    def get_structure(self):
        ret = {"columns": {}}
        table = self.get_table()
        for column in table.columns:
            if hasattr(column, 'type'):
                c_type = ColTypeToStr(column.type)
            else:
                c_type = None
            ret['columns'][column.name] = c_type
        ret['key'] = table.primary_key.columns.values()[0].name
        return ret
    def __str__(self):
        return self.source_database.handle + '.' + self.source_table
    def clean(self):
        from .methods import exec_query
        if not hasattr(self, 'source_database'):
            raise ValidationError('Please select source database')
        if not hasattr(self, 'source_table') or len(self.source_table) < 3:
            raise ValidationError('Please select source table')
        for bt in SourceTable.objects.all():
            if(str(bt) == str(self)):
                raise ValidationError('Table \'{0}\' already declared as source table.'.format(str(self)))
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
        metaid_table = '{0}.{1}'.format(self.source_database.pk, schema)
        metaid_pdr = '{0}.{1}'.format(self.source_database.pk, None)
        if metaid_table in cached_database_metas:
            del cached_database_metas[metaid_table]
        if metaid_pdr in cached_database_metas:
            del cached_database_metas[metaid_pdr]
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
        super(SourceTable, self).delete()

class Reflection(models.Model):
    description = models.CharField(max_length=500)
    source_table = models.ForeignKey(SourceTable, on_delete=models.CASCADE)       # The source table
    destination_database = models.ForeignKey(Database, on_delete=models.CASCADE)        # The destination datastorage
    destination_table = models.CharField(max_length=500)
    last_commit = models.IntegerField(help_text='id of last pdr_event executed', blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField('Active', help_text='Means that the reflection will be updated whenever the source table is updated', default=True)
    ignore_delete_events = models.BooleanField('Ignore Delete Events', help_text='Don\'t delete records in the reflection when they\'re deleted in the source.', default=True)
    source_fields = models.CharField(help_text='json representation of the structure of the source table (read only)', max_length=10000)
    destination_fields = models.CharField(help_text='json configuration that represents the translation from source data to destination structure', max_length=10000)
    reflection_statment = models.CharField(help_text='SQL statment that will be used to input the data into the destination table whenever the source changes', max_length=10000)
    def get_destination_table(self):
        dest_table_path = self.destination_table.split('.')
        dest_table_path.reverse()
        destination_table = self.destination_database.get_table(*dest_table_path)
        return destination_table
    def get_source_table(self):
        return self.source_table.get_table()
    def bulk_upsert(self, lst):
        print(self, 'Saving {0} items'.format(len(lst)))
        destination_dbc = self.destination_database.mount().connect()
        destination_table = self.get_destination_table()
        json_config = json.loads(self.destination_fields)
        if "key_binding" in json_config:
            for key in json_config["key_binding"]:
                source_key = key
                destination_key = json_config["key_binding"][source_key]
        else:
            source_key = None
            destination_key = None
        source_table = self.get_source_table()
        source_table_pk = source_table.primary_key.columns.values()[0]
        destination_table_pk = destination_table.primary_key.columns.values()[0]
        # List missing records
        if source_key:
            targer_ids = [rec[source_key] for rec in lst]
            stmt = select([destination_table.c[destination_key]], destination_table.c[destination_key].in_(targer_ids))
        else:
            targer_ids = [rec[source_table_pk.name] for rec in lst]
            stmt = select([destination_table_pk], destination_table_pk.in_(targer_ids))
        already_existing_records = [rec[0] for rec in destination_dbc.execute(stmt).fetchall()]
        index_of_already_existing_records = {}
        missing_records = []
        for rec in already_existing_records:
            index_of_already_existing_records[rec] = 'EXISTS'
        for rec in targer_ids:
            if rec not in already_existing_records:
                missing_records.append(rec)
        # Create missing records
        if source_key:
            insert_data = [{destination_key : item} for item in missing_records]
        else:
            insert_data = [{destination_table_pk.name : item} for item in missing_records]
        if len(missing_records) > 0:
            destination_dbc.execute(destination_table.insert(), insert_data)
        # run update statments for each record
        if len(targer_ids) > 0:
            destination_dbc.execute(
                text(self.reflection_statment),
                lst
            )
        print(self, 'Done Saving')
    def bulk_delete(self, lst):
        print(self, 'Deleting {0} items'.format(len(lst)))
        destination_dbc = self.destination_database.mount().connect()
        destination_table = self.get_destination_table()
        destination_table_pk = destination_table.primary_key.columns.values()[0]
        targer_ids = lst
        limit = 500
        start = 0
        while start < len(lst):
            targer_ids = lst[start:start+limit]
            destination_dbc.execute(
                destination_table.delete(destination_table_pk.in_(targer_ids))
            )
            start += limit
        print(self, 'Done Deleting')
    def dump(self):
        source_dbc = self.source_table.source_database.mount().connect()
        source_table = self.get_source_table()
        source_pdr_table = self.source_table.get_pdr_table()
        # Check if we have any pdr events for this broadcaster and update "last_commit"
        ret = source_dbc.execute(
            source_pdr_table.select().order_by(desc(source_pdr_table.c.id)).limit(1)
        ).fetchall()
        if len(ret):
            commit = dict(ret[0])
            self.last_commit = commit['id']
            self.last_updated = timezone.make_aware(
                commit['c_time'],
                timezone=pytz.timezone("UTC")
            )
        # Retrive all existing data and mirror it
        data = source_dbc.execute(source_table.select()).fetchall()
        data = [dict(rec) for rec in data]
        if len(data) > 0:
            self.bulk_upsert(data)
        self.save()
    def reflect(self):
        self = Reflection.objects.get(pk=self.pk)
        source_dbc = self.source_table.source_database.mount().connect()
        # Read SourceTable's latest pdr_events
        pdr_table = self.source_table.get_pdr_table()
        data_table = self.source_table.get_table()
        data_table_pk = data_table.primary_key.columns.values()[0]
        upsert_stmt = pdr_table.select().with_only_columns([
            func.max(pdr_table.c.id).label('{0}_id'.format(pdr_prefix)),
            func.max(pdr_table.c.c_action).label('{0}_c_action'.format(pdr_prefix)),
            pdr_table.c.c_record.label('{0}_c_record'.format(pdr_prefix)),
            func.max(pdr_table.c.c_time).label('{0}_c_time'.format(pdr_prefix))
        ])
        if self.last_commit:
            upsert_stmt = upsert_stmt.where(pdr_table.c.id > self.last_commit)
        upsert_stmt = upsert_stmt.group_by(pdr_table.c.c_record)
        upsert_stmt = upsert_stmt.order_by('{0}_id'.format(pdr_prefix))
        upsert_stmt = alias(upsert_stmt, 'pdr')
        upsert_stmt = upsert_stmt.join(data_table, upsert_stmt.c['{0}_c_record'.format(pdr_prefix)] == data_table_pk)
        upsert_stmt = select([upsert_stmt])
        ret = source_dbc.execute(upsert_stmt)
        def retrive_data_record(commit):
            data_record = commit.copy()
            data_record.pop('{0}_id'.format(pdr_prefix))
            data_record.pop('{0}_c_action'.format(pdr_prefix))
            data_record.pop('{0}_c_record'.format(pdr_prefix))
            data_record.pop('{0}_c_time'.format(pdr_prefix))
            return data_record
        commits = [dict(commit) for commit in ret.fetchall()]
        #if len(commits) > 0:
            #print(self, '{0} new events detected'.format(len(commits)))
        upserts = [retrive_data_record(commit) for commit in commits if commit['{0}_c_action'.format(pdr_prefix)] in ['INSERT', 'UPDATE']]
        deletes = [commit['{0}_c_record'.format(pdr_prefix)] for commit in commits if commit['{0}_c_action'.format(pdr_prefix)] == 'DELETE']
        if len(upserts) > 0:
            self.bulk_upsert(upserts)
        if len(deletes) > 0:
            if self.ignore_delete_events:
                print(self, 'Ignoring {0} delete events'.format())
            else:
                self.bulk_delete(deletes)
        if len(commits) > 0:
            self.last_commit = commits[-1]['{0}_id'.format(pdr_prefix)]
            self.last_updated = timezone.make_aware(
                commits[-1]['{0}_c_time'.format(pdr_prefix)],
                timezone=pytz.timezone("UTC")
            )
            self.save()
    def __str__(self):
        return '{0}-->{1}.{2} : {3}'.format(self.source_table,self.destination_database, self.destination_table, self.description)
    def clean(self):
        destTablePath = self.destination_table.split('.')
        destTablePath.reverse()
        if len(destTablePath) == 1:
            table = destTablePath[0]
            schema = None
        elif len(destTablePath) == 2:
            table = destTablePath[0]
            schema = destTablePath[1]
        else:
            raise ValidationError('Invalid table path: {0}'.format(destTablePath))
        try:
            destination_fields = json.loads(self.destination_fields)
        except Exception as e:
            raise ValidationError('Unable to parse json: {0}'.format(self.destination_fields))
        ddb = self.destination_database.mount()
        destinationTable = self.destination_database.get_table(table, schema)
        if destinationTable != None:
            # Table already exists, check its compatiblity
            print(self, 'Table {0} already exists'.format(destinationTable))
            pk_name = destinationTable.primary_key.columns.values()[0].name
            if destination_fields['key'] != pk_name:
                raise ValidationError(
                    'Table \'{0}\' already exists but its primary key is \'{1}\' rather than \'{2}\''
                    .format(self.destination_table, pk_name, destination_fields['key'])
                )
            for needed_column in destination_fields['columns']:
                c_type = destination_fields['columns'][needed_column]
                if needed_column not in destinationTable.columns:
                    print(self, 'Adding column {0} to table {1}'.format(needed_column, destinationTable))
                    ColumnObj = Column(
                        needed_column, 
                        StrToColType(c_type),
                        nullable = True
                    )
                    add_column(ddb, self.destination_table, ColumnObj)
            # Check PK name and type
        else:
            # Table not defined, create table
            print(self, 'Creating table {0} in database {1}'.format(table, self.destination_database))
            try:
                meta = MetaData()
                tablecolumns = []   
                for col in destination_fields['columns']:
                    ispk = col == destination_fields['key']
                    tablecolumns.append(
                        Column(col, StrToColType(destination_fields['columns'][col]), nullable = not ispk, primary_key = ispk)
                    )
                Table(
                    table, meta,
                    *tablecolumns,
                    schema=schema
                )
                meta.create_all(ddb)
            except Exception as e:
                raise ValidationError('Failed to create table: {0}'.format(e))
        # Delete destination schema's meta cache to force reloading new updates
        del cached_database_metas['{0}.{1}'.format(self.destination_database.pk, schema)]
        self.save()
        self.dump()
        self.refresh()
    def stop(self):
        self.active = False
        self.save()
    def reflection_loop(self):
        active = Reflection.objects.get(pk=self.pk).active
        if active:
            WAIT_SECONDS = 1
            try:
                self.reflect()
            except Exception as e:
                print('Failed to perform reflection ', self)
                print(e)
            t = threading.Timer(WAIT_SECONDS, self.reflection_loop)
            t.daemon = True
            t.start()
        else:
            del pdr_reflection_loops['Reflection_loop_{0}'.format(self.pk)]
    def start(self):
        self.active = True
        self.save()
    def refresh(self):
        active = Reflection.objects.get(pk=self.pk).active
        if active and 'Reflection_loop_{0}'.format(self.pk) not in pdr_reflection_loops:
            pdr_reflection_loops['Reflection_loop_{0}'.format(self.pk)] = True
            t = threading.Timer(1, self.reflection_loop)
            t.daemon = True
            t.start()
