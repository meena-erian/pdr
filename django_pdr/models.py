from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import *
from .datasources import datasources
import urllib.parse
import json
import pytz
import pgcrypto
import logging


pdr_prefix = 'pdr_event'
cached_database_metas = {}
database_engines = {}

# logging.basicConfig(level=logging.DEBUG)


def get_table_key(table, obj=False):
    """This function takes an SQLAlchemy table object and returns its
    primary key, or if the table has no primary key, it returns its
    first foreign key. Otherwise, it raises a ValidationError

    Args:
        table (SQLAlchemy.Table): An SQLAlchemy table object
        obj (bool, optional): Whether the function is expected to return
            an SQLAlchemy Column object. Otherwise, it returns a string, the
            column name. Defaults to False.

    Raises:
        ValidationError: When the table has no key columns.

    Returns:
        (SQLAlchemy.Column|str): Returns either the SQLAlchemy Column object
        or the column name of the key column of the provided table.
    """
    primary_key_columns = table.primary_key.columns.values()
    if len(primary_key_columns):
        key = primary_key_columns[0]
    else:
        foreign_keys = list(table.foreign_keys)
        if len(foreign_keys):
            key = foreign_keys[0].column
        else:
            raise ValidationError(
                'Table {0} has no primary key or even foreign key'
                .format(table)
            )
    if obj:
        return key
    return key.name


def add_column(engine, table_name, column):
    """This function is used to add a new field to an already
    existing table in a database.

    Args:
        engine (SQLAlchemy.Engine): Database engine object
        table_name (str): full dottedpath.name of the target table
        column (SQLAlchemy.Column): Column object that will be added
    """
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    engine.execute(
        'ALTER TABLE %s ADD COLUMN %s %s NULL' % (
            table_name,
            column_name,
            column_type
        )
    )


def typeFullName(o):
    """This function takes any user defined object or class of any type and
    returns a string absolute identifier of the provided type.

    Args:
        o (Any): object of any type to be inspected

    Returns:
        str: The full dotted path of the provided type
    """
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + o.__class__.__name__


def ColTypeToStr(Type):
    """
    This function takes an SQLAlchemy Column type and returns a string
    identifier of that type after validating that it is a valid
    SQLAlchemy column type.

    This function is the inverse of the function StrToColType.

    @param Type: SQLAlchemy Column type
    @returns: str, String uniquely identifying the provided Column type
    """
    instanceClassName = typeFullName(Type)
    mainParent, path = instanceClassName.split('.', 1)
    if mainParent != 'sqlalchemy':
        raise Exception('Invalid type for SQL')
    if hasattr(Type, 'length') and Type.length is not None:
        path += '({0})'.format(Type.length)
    return path


def StrToColType(TypePath):
    """This function takes a string SQLAlchemy Column type identifier
    and returns an SQLAlchemy type definition class of the provided type.

    This function is the inverse of the function ColTypeToStr.

    Args:
        TypePath (str): The string identifier of an SQLAlchemy column type.

    Returns:
        class: the SQLAlchemy column class of the provided string
    """
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


class Database(models.Model):
    """
    This data model describes a database connection information and it
    provides functions to interact with databases.
    """
    handle = models.SlugField(
        max_length=200,
        help_text='Set a unique name for this database'
    )
    source = models.IntegerField(
        choices=datasources.touple,
        help_text='Select what kind of SQL database this is'
    )
    config = pgcrypto.EncryptedTextField(
        max_length=1000,
        help_text='Set connection information and credentials'
    )
    description = models.CharField(
        max_length=200,
        help_text='Describe what this database is all about'
    )

    def __str__(self):
        return self.handle

    def configs():
        return datasources.__list__

    def mount(self):
        """
        This function returns an instance of an SQLAlchemy database_engine of
         the database configured in the object calling the method.

        For perfomance, each time this function is called, it saves a copy of
         the engine in the database_engines dictionary so that when it's called
         again for the same database, it will first look in the dictionary and
         if it find that the engine is already saved there, it will return it

        """
        if str(self.pk) in database_engines:
            # Run garbage collector to dispose old IDLE connections
            # database_engines[str(self.pk)].dispose()
            return database_engines[str(self.pk)]
        config = json.loads(self.config)
        connectionStr = datasources.__list__[self.source]['dialect'] + '://'
        if 'dbfile' in config:
            connectionStr += '/' + config['dbfile']
        else:
            connectionStr += (
                urllib.parse.quote_plus(config['user'])
                + ":"
                + urllib.parse.quote_plus(config['password'])
                + "@"
            )
            connectionStr += config['host']
            if "port" in config:
                connectionStr += ":"
                connectionStr += str(config["port"])
            connectionStr += "/" + config["dbname"]
        database_engines[str(self.pk)] = create_engine(
            connectionStr,
            echo=False
        )
        return database_engines[str(self.pk)]

    def tables(self):
        """
        This function returns a list of all tables in the database from which
         the function is being called.
        """
        from .methods import make_query
        with self.mount().connect() as connection:
            results = []
            if self.source == datasources.SQLIGHT:
                ret = connection.execute(make_query(datasources.__list__[
                    self.source]['dialect'] + '/list_tables'))
            else:
                ret = connection.execute(make_query('list_tables'))
            for record in ret:
                results.append(record[0])
            return results

    def meta(self, schema=None, refresh=False):
        """
        This function returns an SQLAlchemy database MetaData object of the
         database from which the function is being called.

        For perfomance, each time this function is called, it saved a copy
         of the MetaData object in the cached_database_metas dictionary so
         that when it's called again for the same database, it will first
         look in the dictionary and if it found that the MetaDate is already
         saved there, it will return it directly from there.

        Parameters
        ----------
            schema (str | None): The schema name to get the MetaData for.
                Default is 'public'

            refresh (boolean): Whether to reload the MetaData from the
                server or use the cached copy instead for performance.
        """
        db = self.mount()
        metaid = '{0}.{1}'.format(self.pk, schema)
        if metaid in cached_database_metas and not refresh:
            return cached_database_metas[metaid]
        else:
            logging.debug(
                'Loading meta data for {0} schema {1}'
                .format(self, schema)
            )
            cached_database_metas[metaid] = MetaData(schema=schema)
            cached_database_metas[metaid].reflect(bind=db)
            return cached_database_metas[metaid]

    def get_table(self, table, schema=None, refresh=False):
        """
        This function returns an SQLAlchemy Table object for the table
         identified by 'table', and 'schema' (optional)

        Parameters
        ----------
            table (str): The name of the table to retrive

            schema (str | None): The schema containing the intended table.
                Default is None, which refers to the public schema.

            refresh (boolean): Whether to load the table structure from the
                database or to use the cached meta data instead
                for performance.
        """
        meta = self.meta(schema, refresh=refresh)
        if(len(meta.tables.keys()) < 1):
            raise Exception(
                'Exception in function Database.get_table. '
                '{0}.meta() returned an empty structure'
                .format(self)
            )
        if schema is not None:
            table = schema + '.' + table
        if table in meta.tables:
            return meta.tables[table]
        else:
            return None

    def clean(self):
        """
        This function is used to validate database connection information
         before saving it.
        """
        try:
            with self.mount().connect() as connection:
                None  # Just testing the connection
        except Exception as e:
            raise ValidationError(
                'Failed to connect to database: {0}'.format(e))


class SourceTable(models.Model):
    """
    A source table is a table that updates other tables, typically in other
     databases when any records of that table are added, removed, or modified.

    Any existing database table in any database connected to the PDR server
     can be added as a SourceTable. Once added, it's being monitored by the
     PDR server; so that whenever any changes occur in any record in that
     table, the PDR server will be notifed in order to update reflections.

    When a talbe is added as a source table, trigger function are installed
    inside the database intself, so that whenever any INSERT, UPDATE, or DELETE
    events occure on any record in that table, the functions insert a record to
    a pdr_event table inside the same database which is being used to record
    the history of changes of that table. Each record in the pdr_event table
    records what event has occured, (INSERT UPDATE OR DELETE) the timestamp
    at which the event has occured, and the record affected is being identified
    by the value of its primary key column. That's why source tables must have
    a primary key column for a reliable way to refer to each individual record.
    """
    source_database = models.ForeignKey(Database, on_delete=models.CASCADE)
    source_table = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)

    def get_table(self, refresh=False):
        """
        Retrives the SQLAlchemy Table object of the source table from which
         the function was called.

        Parameters
        ----------

            refresh (boolean): Whether to load the table structure from the
                database or to use cached meta data instead for performance.

        Returns
        -------
            Class(SQLAlchemy.Table)
        """
        path = self.source_table.split('.')
        path.reverse()
        ret = self.source_database.get_table(*path, refresh=refresh)
        if type(ret).__name__ != 'Table':
            raise Exception(
                'Exception in function SourceTabl.get_table. '
                ' {0}.get_table({1}) returned {2}'.format(
                    self.source_database,
                    path,
                    ret
                )
            )
        return ret

    def get_pdr_table(self, refresh=False):
        """
        Retrives the notification channel Table object (AKA pdr_table) of the
         source table from which the function was called.

        Parameters
        ----------

            refresh (boolean): Whether to load the table structure from the
                database or to use cached meta data instead for performance.

        Returns
        -------
            Class(SQLAlchemy.Table)
        """
        table_path = self.source_table.split('.')
        if len(table_path) == 1:
            table_path.insert(0, 'None')
        pdr_table_name = '{0}_o_{1}_o_{2}'.format(pdr_prefix, *table_path)
        return self.source_database.get_table(pdr_table_name, refresh=refresh)

    def get_structure(self, refresh=False):
        """
        Retrives a dict object describing the structure of the source table
         from which the function was called.

        Parameters
        ----------

            refresh (boolean): Whether to load the table structure from the
                database or to use cached meta data instead for performance.

        Returns
        -------
            dict:
        """
        ret = {"columns": {}}
        table = self.get_table(refresh=refresh)
        if type(table).__name__ != 'Table':
            raise Exception(
                'Exceeption in function SourceTable. get_structure.'
                ' {0}.get_table returned type {1}'
                .format(
                    self,
                    type(table).__name__
                )
            )
        for column in table.columns:
            if hasattr(column, 'type'):
                c_type = ColTypeToStr(column.type)
            else:
                c_type = None
            ret['columns'][column.name] = c_type
        ret['key'] = get_table_key(table)
        return ret

    def __str__(self):
        return self.source_database.handle + '.' + self.source_table

    def clean(self):
        """
        This function installs SQL trigger functions and creates a
         notification channel table in the source database once a new
         source table is defined. The trigger functions are configured
         to update notification channel table (AKA pdr_table) whenever
         any changes occur in the source table.
        """
        from .methods import exec_query
        if not hasattr(self, 'source_database'):
            raise ValidationError('Please select source database')
        if not hasattr(self, 'source_table') or len(self.source_table) < 3:
            raise ValidationError('Please select source table')
        for bt in SourceTable.objects.all():
            if(str(bt) == str(self)):
                raise ValidationError(
                    'Table \'{0}\' already declared as source table.'
                    .format(str(self))
                )
        # Check if selected table exists in selected database. if not
        # raise ValidationError
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
            table_obj = Table(
                table,
                MetaData(),
                autoload=True,
                autoload_with=db,
                schema=schema
            )
        except Exception as e:
            raise ValidationError('Table not found: {0}'.format(e))
        key = get_table_key(table_obj, obj=True)
        pdr_table_name = '{0}_o_{1}_o_{2}'.format(pdr_prefix, schema, table)
        meta = MetaData()
        pdr_event = Table(
            pdr_table_name, meta,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('c_action', String(6)),
            Column('c_record', key.type),
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
            (
                datasources
                .__list__
                [self.source_database.source]['dialect']
                + '/create_event_listener'
            ),
            pdr_prefix,
            schema,
            table,
            key.name
        )

    def delete(self):
        """
        This function is meant to delete the pdr table and the trigger
         functions that was initially created by the 'clean()' function.
        """
        from .methods import exec_query
        table_path = self.source_table.split('.')
        if len(table_path) == 1:
            schema = None
            table = table_path[0]
        elif len(table_path) == 2:
            schema, table = table_path
        db = self.source_database.mount()
        # try to remove event listeners from the databases table.
        # If failed, raise ValidationError
        exec_query(
            db,
            (
                datasources
                .__list__
                [self.source_database.source]['dialect']
                + '/delete_event_listener'
            ),
            pdr_prefix,
            schema,
            table
        )
        super(SourceTable, self).delete()


class Reflection(models.Model):
    """A Reflection is a group of configurations and instructions that
    describe a replication of a table. Minimally, a reflection describes
    the destination database and the destination table to which data will
    be replicated and the source table from which data will be retrived.
    And by default, the destination table will have the same columes as
    the source table from which it's being replicated. However, PDR provdes
    more advanced option to customize the structure of the destination table
    which keeping it up-to-date with its source table.

    A reflection is described by the following three strings:
        source_fields:
            This field describes the structure of the source table (a list of
            column names and data types and defines which column is the
            primarykey)
            source_fields are auto generated from the source database and
            cannot be modified

        destination_table:
            The name of the destination table. (it will be created if it
            didn't exist)

        destination_fields:
            This field descibes the structure of the destination table and it's
            being used to create the table if it did not exist or to add
            columns to it if it already existed but didn't contain all the
            columns listed in the destination_table

            Note: The table can contain more columns than that listed in
                destination_fields. However, it must have the same primary
                key as configured in the destination_fields variable.

            key_binding: In addition to the columns, and the primary key,
                there's a key_binding optional variable defined in the
                destination_fields object. The syntax for this variable is:
                { source_key : destination_key }
                By default, source_key will be the name of the primary key
                column name of the source table, and destination_key will be
                the name of the primary key column name of the destination
                table. However, if the column intended to be the primary key
                for the destination table is not the same as that of the
                source table, we might have some trouble applying the
                replication because PDR needs to be able to identify each
                idividual record in the destination table and match it with
                the record it came from in the source table. That's why
                key_binding must be used when the source and destination
                talbes has different primary key columns.

                Conditions:
                ----------
                The following conditions must be met when using key_binding

                    1. Both of the source_key and the destination_key must be
                        of the same data type.
                    2. destination_key must be the only required field in the
                        destination table because during replication, the
                        PDR server while chech which records exist and which
                        doesn't based on the value of that column and will
                        create non-existing records by inserting nothing but
                        the destination_key field for these records.
                        Tl;Dr: destination_key must be the primary key of the
                        destination table.

        reflection_statment:
            reflection_statment is an SQL update statment applied on every
        record in the destination table to reflect the changes on that table.
        The reflection statment is manipulated using SQLALchemy's bindparams
        function with the values of each column in source_fields before
        sending the query to the server.
    """
    description = models.CharField(max_length=500)
    source_table = models.ForeignKey(  # The source table
        SourceTable,
        on_delete=models.CASCADE
    )
    destination_database = models.ForeignKey(  # The destination datastorage
        Database,
        on_delete=models.CASCADE
    )
    destination_table = models.CharField(max_length=500)
    last_commit = models.IntegerField(
        help_text='id of last pdr_event executed',
        blank=True,
        null=True
    )
    last_updated = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(
        'Active',
        help_text=(
            'Means that the reflection will be updated whenever'
            + ' the source table is updated'
        ),
        default=True
    )
    ignore_delete_events = models.BooleanField(
        'Ignore Delete Events',
        help_text=(
            'Don\'t delete records in the reflection when they\'re'
            + ' deleted in the source.'
        ),
        default=True
    )
    source_fields = models.CharField(
        help_text=(
            'json representation of the structure of the'
            + 'source table (read only)'
        ),
        max_length=10000
    )
    destination_fields = models.CharField(
        help_text=(
            'json configuration that represents the translation from'
            + ' source data to destination structure'
        ),
        max_length=10000
    )
    reflection_statment = models.CharField(
        help_text=(
            'SQL statment that will be used to input the data into the'
            + ' destination table whenever the source changes'
        ),
        max_length=10000
    )

    def get_destination_table(self, refresh=False):
        """
        Parameters
        ----------

            refresh (boolean): Whether to load the table structure from the
                database or to use cached meta data instead for performance.

        Returns
        -------
            Class(SQLAlchemy.Table)
        """
        dest_table_path = self.destination_table.split('.')
        dest_table_path.reverse()
        destination_table = self.destination_database.get_table(
            *dest_table_path, refresh=refresh)
        return destination_table

    def get_source_table(self, refresh=False):
        return self.source_table.get_table(refresh=refresh)

    def get_destination_structure(self):
        return json.loads(self.destination_fields)

    def get_source_structure(self):
        return json.loads(self.source_fields)

    def get_destination_key(self):
        destination_table = self.get_destination_table()
        destination_structure = self.get_destination_structure()
        destination_key_name = destination_structure['key']
        return destination_table.c[destination_key_name]

    def get_source_key(self):
        source_table = self.get_source_table()
        source_structure = self.get_source_structure()
        source_key_name = source_structure['key']
        return source_table.c[source_key_name]

    def bulk_upsert(self, lst):
        logging.debug(
            '{0} Saving {1} items'
            .format(self, len(lst))
        )
        destination_db_engine = self.destination_database.mount()
        logging.debug('{0} retriving destination table'.format(self))
        destination_table = self.get_destination_table()
        logging.debug('{0} retriving json config'.format(self))
        json_config = json.loads(self.destination_fields)
        if "key_binding" in json_config:
            for key in json_config["key_binding"]:
                source_key = key
                destination_key = json_config["key_binding"][source_key]
        else:
            source_key = None
            destination_key = None
        logging.debug('{0} retriving source table'.format(self))
        source_table = self.get_source_table()
        logging.debug('{0} retriving source PK'.format(self))
        source_table_key = get_table_key(source_table, obj=True)
        logging.debug('{0} retriving destination PK'.format(self))
        destination_table_key = get_table_key(destination_table)
        # List missing records
        already_existing_records = []
        logging.debug('{0} listing already existing records'.format(self))
        limit = 500
        start = 0
        if source_key:
            targer_ids = [rec[source_key] for rec in lst]
            ids_to_select = targer_ids.copy()
            while start < len(ids_to_select):
                logging.debug('{0} listing records from {1}, to {2}'.format(
                    self,
                    start,
                    start+limit
                ))
                selected_ids = ids_to_select[start:start+limit]
                with destination_db_engine.connect() as destination_dbc:
                    ret = destination_dbc.execute(
                        select(
                            [destination_table.c[destination_key]],
                            destination_table.c[destination_key]
                            .in_(selected_ids)
                        )
                    ).fetchall()
                already_existing_records.extend([rec[0] for rec in ret])
                start += limit
        else:
            targer_ids = [rec[source_table_key.name] for rec in lst]
            ids_to_select = targer_ids.copy()
            while start < len(ids_to_select):
                logging.debug('{0} listing records from {1}, to {2}'.format(
                    self,
                    start,
                    start+limit
                ))
                selected_ids = ids_to_select[start:start+limit]
                with destination_db_engine.connect() as destination_dbc:
                    ret = destination_dbc.execute(
                        select(
                            [destination_table_key],
                            destination_table_key
                            .in_(selected_ids)
                        )
                    ).fetchall()
                already_existing_records.extend([rec[0] for rec in ret])
                start += limit
        index_of_already_existing_records = {}
        missing_records = []
        logging.debug(
            '{0} {1} records already exists. Selecting missing records'
            .format(
                self,
                len(already_existing_records)
            )
        )
        for rec in already_existing_records:
            index_of_already_existing_records[rec] = 'EXISTS'
        for rec in targer_ids:
            if rec not in index_of_already_existing_records:
                missing_records.append(rec)
        logging.debug(
            '{0} {1} missing records were identified'
            .format(self, len(missing_records))
        )
        # Create missing records
        if source_key:
            insert_data = [{destination_key: item} for item in missing_records]
        else:
            insert_data = [{destination_table_key.name: item}
                           for item in missing_records]
        if len(missing_records) > 0:
            logging.debug(
                '{0} Creating {1} missing records'
                .format(self, len(missing_records))
            )
            with destination_db_engine.connect() as destination_dbc:
                destination_dbc.execute(
                    destination_table.insert(),
                    insert_data
                )
        else:
            logging.debug(
                '{0} All recrods already exists. Updating records data'
                .format(self)
            )
        # run update statments for each record
        if len(lst) > 0:
            logging.debug(
                '{0} Updating data for {1} records'
                .format(self, len(lst))
            )
            limit = 500
            start = 0
            while start < len(lst):
                logging.debug(
                    '{0} Updating records from {1}, to {2}'
                    .format(self, start, start+limit)
                )
                selected_items = lst[start:start+limit]
                with destination_db_engine.connect() as destination_dbc:
                    destination_dbc.execute(
                        text(self.reflection_statment),
                        selected_items
                    )
                start += limit
        logging.debug('Done Saving'.format(self))

    def bulk_delete(self, lst):
        logging.debug(
            '{0} Deleting {1} items'
            .format(self, len(lst))
        )
        destination_table = self.get_destination_table()
        destination_table_key = get_table_key(destination_table, obj=True)
        targer_ids = lst
        limit = 500
        start = 0
        with self.destination_database.mount().connect() as destination_dbc:
            while start < len(lst):
                targer_ids = lst[start:start+limit]
                destination_dbc.execute(
                    destination_table.delete(
                        destination_table_key
                        .in_(targer_ids)
                    )
                )
                start += limit
        logging.debug('Done Deleting'.format(self))

    def dump(self):
        with self.source_table.source_database.mount().connect() as source_dbc:
            source_table = self.get_source_table()
            source_pdr_table = self.source_table.get_pdr_table()
            # Check if we have any pdr events for this source and
            # update "last_commit"
            ret = source_dbc.execute(
                source_pdr_table
                .select()
                .order_by(desc(source_pdr_table.c.id))
                .limit(1)
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
        # db.close_old_connections()
        logging.debug('{0}: Reflecting changes'.format(self))
        self = Reflection.objects.get(pk=self.pk)
        logging.debug(
            '{0}: Connecting to source database to perform reflection'
            .format(self)
        )
        # Read SourceTable's latest pdr_events
        logging.debug(
            '{0}: Retriving tables meta information to perform reflection'
            .format(self)
        )
        pdr_table = self.source_table.get_pdr_table()
        data_table = self.source_table.get_table()
        data_table_key = get_table_key(data_table, obj=True)
        upsert_stmt = pdr_table.select().with_only_columns([
            func.max(pdr_table.c.id).label('{0}_id'.format(pdr_prefix)),
            func.max(pdr_table.c.c_action).label(
                '{0}_c_action'.format(pdr_prefix)),
            pdr_table.c.c_record.label('{0}_c_record'.format(pdr_prefix)),
            func.max(pdr_table.c.c_time).label('{0}_c_time'.format(pdr_prefix))
        ])
        if self.last_commit:
            upsert_stmt = upsert_stmt.where(pdr_table.c.id > self.last_commit)
        upsert_stmt = upsert_stmt.group_by(pdr_table.c.c_record)
        upsert_stmt = upsert_stmt.order_by('{0}_id'.format(pdr_prefix))
        upsert_stmt = alias(upsert_stmt, 'pdr')
        upsert_stmt = upsert_stmt.join(
            data_table,
            upsert_stmt.c['{0}_c_record'.format(pdr_prefix)]
            == self.get_source_key()
        )
        upsert_stmt = select([upsert_stmt])
        with self.source_table.source_database.mount().connect() as source_dbc:
            ret = source_dbc.execute(upsert_stmt)
            commits = [dict(commit) for commit in ret.fetchall()]

        def retrive_data_record(commit):
            data_record = commit.copy()
            data_record.pop('{0}_id'.format(pdr_prefix))
            data_record.pop('{0}_c_action'.format(pdr_prefix))
            data_record.pop('{0}_c_record'.format(pdr_prefix))
            data_record.pop('{0}_c_time'.format(pdr_prefix))
            return data_record

        upserts = [
            retrive_data_record(commit) for commit in commits
            if commit[
                '{0}_c_action'.format(pdr_prefix)
            ] in ['INSERT', 'UPDATE']
        ]
        deletes = [
            commit['{0}_c_record'.format(pdr_prefix)] for commit in commits
            if commit['{0}_c_action'.format(pdr_prefix)] == 'DELETE'
        ]
        if len(upserts) > 0:
            self.bulk_upsert(upserts)
        if len(deletes) > 0:
            if self.ignore_delete_events:
                logging.debug(
                    '{0} Ignoring {1} delete events'
                    .format(self, len(deletes))
                )
            else:
                self.bulk_delete(deletes)
        if len(commits) > 0:
            self.last_commit = commits[-1]['{0}_id'.format(pdr_prefix)]
            self.last_updated = timezone.make_aware(
                commits[-1]['{0}_c_time'.format(pdr_prefix)],
                timezone=pytz.timezone("UTC")
            )
            self.save()
        return len(commits)

    def __str__(self):
        return '{0}-->{1}.{2} : {3}'.format(
            self.source_table,
            self.destination_database,
            self.destination_table,
            self.description
        )

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
            raise ValidationError(
                'Invalid table path: {0}'.format(destTablePath))
        try:
            destination_fields = json.loads(self.destination_fields)
        except Exception as e:
            raise ValidationError(
                'Unable to parse json: {0}'.format(self.destination_fields))
        ddb = self.destination_database.mount()
        destinationTable = self.destination_database.get_table(
            table,
            schema,
            refresh=True
        )
        if destinationTable is not None:
            # Table already exists, check its compatiblity
            logging.info(
                '{0} Table {1} already exists'
                .format(self, destinationTable)
            )
            key_name = get_table_key(destinationTable)
            if destination_fields['key'] != key_name:
                raise ValidationError(
                    'Table \'{0}\' already exists but its primary key is \
                    \'{1}\' rather than \'{2}\''
                    .format(
                        self.destination_table,
                        key_name,
                        destination_fields['key']
                    )
                )
            for needed_column in destination_fields['columns']:
                c_type = destination_fields['columns'][needed_column]
                if needed_column not in destinationTable.columns:
                    logging.info(
                        '{0} Adding column {1} to table {2}'
                        .format(self, needed_column, destinationTable)
                    )
                    ColumnObj = Column(
                        needed_column,
                        StrToColType(c_type),
                        nullable=True
                    )
                    add_column(ddb, self.destination_table, ColumnObj)
            # Check PK name and type
        else:
            # Table not defined, create table
            logging.info(
                '{0} Creating table {1} in database {2}'
                .format(self, table, self.destination_database)
            )
            try:
                meta = MetaData()
                tablecolumns = []
                for col in destination_fields['columns']:
                    ispk = col == destination_fields['key']
                    tablecolumns.append(
                        Column(
                            col,
                            StrToColType(
                                destination_fields['columns'][col]
                            ),
                            nullable=not ispk,
                            primary_key=ispk
                        )
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
        del cached_database_metas['{0}.{1}'.format(
            self.destination_database.pk, schema)]
        self.save()
        self.dump()

    def stop(self):
        self.active = False
        self.save()

    def start(self):
        self.active = True
        self.save()
