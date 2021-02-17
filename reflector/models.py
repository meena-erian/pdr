from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from sqlalchemy import *
import urllib.parse
import json
import threading

# Create your models here.
pdr_prefix = 'pdr_event'

def recToDict(rec, table):
    index = 0
    ret = {}
    for c in table.c:
        ret[c.name] = rec[index]
        index += 1
    return ret

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
    if hasattr(Type, 'length'):
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
        if table in meta.tables:
            return meta.tables[table]
        else:
            return None
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
    def upsert(self, id):
        source_dbe = self.source_table.source_database.mount()
        destination_dbe = self.destination_database.mount()
        source_dbc = source_dbe.connect()
        destination_dbc = destination_dbe.connect()
        source_table = self.source_table.get_table()
        dest_table_path = self.destination_table.split('.')
        dest_table_path.reverse()
        destination_table = self.destination_database.get_table(*dest_table_path)
        destination_pk = destination_table.primary_key.columns.values()[0]
        source_pk = source_table.primary_key.columns.values()[0]
        record_reflection = json.loads(self.record_reflection)
        ret = source_dbc.execute(
            source_table.select().where(source_pk == id)
        )
        for rec in ret:
            recDict =recToDict(rec, source_table)
            # Check if the record already exists in destination db
            already_exists = destination_dbc.execute(
                destination_table.select().where(destination_pk == id)
            ).fetchone()
            # Insert or update record
            if already_exists:
                query = record_reflection['update_query']
            else:
                query = record_reflection['insert_query']
            destination_dbc.execute(text(query), **recDict)
    def delete(self, id):
        destination_dbe = self.destination_database.mount()
        destination_dbc = destination_dbe.connect()
        dest_table_path = self.destination_table.split('.')
        dest_table_path.reverse()
        destination_table = self.destination_database.get_table(*dest_table_path)
        destination_pk = destination_table.primary_key.columns.values()[0]
        record_reflection = json.loads(self.record_reflection)
        params = {destination_pk.name : id}
        destination_dbc.execute(text(record_reflection['delete_query']), **params)
    def dump(self):
        source_dbe = self.source_table.source_database.mount()
        source_dbc = source_dbe.connect()
        source_table = self.source_table.get_table()
        source_pdr_table = self.source_table.get_pdr_table()
        source_pk = source_table.primary_key.columns.values()[0]
        # Check if we have any pdr events for this broadcaster and update "last_commit"
        ret = source_dbc.execute(
            source_pdr_table.select().order_by(desc(source_pdr_table.c.id)).limit(1)
        ).fetchall()
        if len(ret):
            ret = ret[0]
            ret = recToDict(ret, source_pdr_table)
            self.last_commit = ret['id']
            self.save()
        ret = source_dbc.execute(source_table.select().with_only_columns([source_pk]))
        for rec in ret:
            print(rec[0])
            self.upsert(rec[0])
    def reflect(self):
        source_dbc = self.source_table.source_database.mount().connect()
        # Read BroadcastingTable's latest pdr_events
        pdr_table = self.source_table.get_pdr_table()
        upsert_stmt = pdr_table.select().with_only_columns([
            func.max(pdr_table.c.id).label('id'),
            func.max(pdr_table.c.c_action).label('c_action'),
            pdr_table.c.c_record,
            func.max(pdr_table.c.c_time).label('c_time')
        ])
        if self.last_commit:
            upsert_stmt = upsert_stmt.where(pdr_table.c.id > self.last_commit)
        upsert_stmt = upsert_stmt.group_by(pdr_table.c.c_record)
        upsert_stmt = upsert_stmt.order_by('id')
        ret = source_dbc.execute(upsert_stmt)
        if len(ret) > 0:
            print(len(ret), " Events retrived")
        for pdr_event in ret:
            pdr_event_obj = recToDict(pdr_event, pdr_table)
            if pdr_event_obj['c_action'] in ['INSERT', 'UPDATE']:
                print(self, '<<<<<<<<<<<UPSERT: {0}'.format(pdr_event_obj['c_record']))
                self.upsert(pdr_event_obj['c_record'])
            if pdr_event_obj['c_action'] == 'DELETE':
                print(self, '<<<<<<<<<<<DELETE: {0}'.format(pdr_event_obj['c_record']))
                self.delete(pdr_event_obj['c_record'])
            self.last_commit = pdr_event_obj['id']
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
        #source_fields = json.loads(self.source_fields)
        record_reflection = json.loads(self.record_reflection)
        ddb = self.destination_database.mount()
        destinationTable = self.destination_database.get_table(table, schema)
        if destinationTable != None:
            # Table already exists, check its compatiblity
            pk_name = destinationTable.primary_key.columns.values()[0].name
            pk_type = ColTypeToStr(destinationTable.primary_key.columns.values()[0].type)
            if record_reflection['key'] != pk_name:
                raise ValidationError(
                    'Table \'{0}\' already exists but its primary key is \'{1}\' rather than \'{2}\''
                    .format(self.destination_table, pk_name, record_reflection['key'])
                )
            #if record_reflection['columns'][record_reflection['key']] != pk_type:
            #    raise ValidationError(
            #        'Table \'{0}\' already exists but primary key \'{1}\' is of type \'{2}\' rather than \'{3}\''
            #        .format(self.destination_table, pk_name, pk_type, record_reflection['columns'][record_reflection['key']])
            #    )
            for needed_column in record_reflection['columns']:
                c_type = record_reflection['columns'][needed_column]
                if needed_column not in destinationTable.columns:
                    ColumnObj = Column(
                        needed_column, 
                        StrToColType(c_type),
                        nullable = True
                    )
                    add_column(ddb, self.destination_table, ColumnObj)
            # Check PK name and type
        else:
            # Table not defined, create table
            try:
                meta = MetaData()
                tablecolumns = []   
                for col in record_reflection['columns']:
                    ispk = col == record_reflection['key']
                    tablecolumns.append(
                        Column(col, StrToColType(record_reflection['columns'][col]), nullable = not ispk, primary_key = ispk)
                    )
                newTable = Table(
                    table, meta,
                    *tablecolumns,
                    schema=schema
                )
                meta.create_all(ddb)
            except Exception as e:
                raise ValidationError('Failed to create table: {0}'.format(e))
        self.dump()
    def start(self):
        WAIT_SECONDS = 3
        self.reflect()
        threading.Timer(WAIT_SECONDS, self.start).start()