from django.core.management.base import BaseCommand
from django_pdr.models import Database, SourceTable, Reflection
import logging
import json
import os


logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Generate source files that can be used to '\
        'recreate the replications strategies'

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--log',
            type=int,
            help='Logging level. (0-5, NOTSET-CRITICAL) default is 3'
        )

    def handle(self, *args, **options):
        log = options['log']
        if isinstance(log, int):
            log = log * 10
            logging.info("Setting log level to {0}".format(log))
            logging.getLogger('root').setLevel(log)
        pwd = os.getcwd()
        pwd = os.path.join(pwd, 'exported_pdr_data')
        databases = os.listdir(os.path.join(pwd, "databases"))
        # os.path.isdir(os.path.join(pwd, "databases"))
        for db_handle in databases:
            db_dir = os.path.join(pwd, "databases", db_handle)
            with open(os.path.join(db_dir, "meta.json")) as file:
                db_meta = json.load(file)
            with open(os.path.join(db_dir, "config.json")) as file:
                db_config = file.read()
            database = Database(
                handle=db_handle,
                source=db_meta["source"],
                description=db_meta["description"],
                pk=db_meta["pk"],
                config=db_config
            )
            logging.info(f"Importing Database {database}")
            database.clean()
            database.save()
        source_tables = os.listdir(os.path.join(pwd, "source_tables"))
        for pk in source_tables:
            source_dir = os.path.join(pwd, "source_tables", pk)
            with open(os.path.join(source_dir, "meta.json")) as file:
                source_meta = json.load(file)
            source = SourceTable(
                pk=int(pk),
                source_database_id=int(source_meta["database"]),
                source_table=source_meta["table"],
                description=source_meta["description"]
            )
            logging.info(f"Importing SourceTable {source}")
            source.clean()
            source.save()
        reflections = os.listdir(os.path.join(pwd, "reflections"))
        for pk in reflections:
            reflection_dir = os.path.join(pwd, "reflections", pk)
            with open(os.path.join(reflection_dir, "meta.json")) as file:
                reflection_meta = json.load(file)
            with open(
                    os.path.join(
                        reflection_dir,
                        "source_fields.json"
                    )) as file:
                source_fields = file.read()
            with open(
                    os.path.join(
                        reflection_dir,
                        "destination_fields.json"
                    )) as file:
                destination_fields = file.read()
            with open(
                    os.path.join(
                        reflection_dir,
                        "reflection_statment.sql"
                    )) as file:
                reflection_statment = file.read()
            reflection = Reflection(
                pk=int(pk),
                description=reflection_meta["description"],
                source_table_id=int(reflection_meta["source_table"]),
                destination_database_id=int(
                    reflection_meta["destination_database"]),
                destination_table=reflection_meta["destination_table"],
                last_commit=reflection_meta["last_commit"],
                # last_updated=reflection_meta["last_updated"],
                active=reflection_meta["active"],
                ignore_delete_events=reflection_meta["ignore_delete_events"],
                source_fields=source_fields,
                destination_fields=destination_fields,
                reflection_statment=reflection_statment
            )
            logging.info(f"Importing Reflection {reflection}")
            reflection.clean()
            reflection.save()
