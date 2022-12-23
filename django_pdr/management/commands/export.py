from django.core.management.base import BaseCommand
from django_pdr.models import Database, SourceTable, Reflection
from json import JSONEncoder
import datetime
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
        os.mkdir(pwd)
        logging.info(f"Created Export Directory {pwd}")
        databases_dir = os.path.join(pwd, "databases")
        os.mkdir(databases_dir)
        logging.info(f"Created Databases Directory {databases_dir}")
        for database in Database.objects.all():
            logging.info(f"Exporting Database {database}")
            db_dir = os.path.join(pwd, "databases", database.handle)
            os.mkdir(db_dir)
            db_meta = {
                "source": database.source,
                "description": database.description,
                "pk": database.pk
            }
            db_config = json.loads(database.config)
            with open(os.path.join(db_dir, "meta.json"), "w") as file:
                file.write(json.dumps(db_meta, indent=4))
            with open(os.path.join(db_dir, "config.json"), "w") as file:
                file.write(json.dumps(db_config, indent=4))
        source_tables_dir = os.path.join(pwd, "source_tables")
        os.mkdir(source_tables_dir)
        logging.info(f"Created SourceTables Directory {source_tables_dir}")
        for source in SourceTable.objects.all():
            logging.info(f"Exporting SourceTabe {source}")
            source_dir = os.path.join(pwd, "source_tables", str(source.pk))
            os.mkdir(source_dir)
            source_meta = {
                "database": source.source_database.pk,
                "table": source.source_table,
                "description": source.description,
            }
            with open(os.path.join(source_dir, "meta.json"), "w") as file:
                file.write(json.dumps(source_meta, indent=4))
        reflections_dir = os.path.join(pwd, "reflections")
        os.mkdir(reflections_dir)
        logging.info(f"Created Reflections Directory {reflections_dir}")
        for reflection in Reflection.objects.all():
            logging.info(f"Exporting Reflection {reflection}")
            reflection_dir = os.path.join(
                pwd,
                "reflections",
                str(reflection.pk)
            )
            os.mkdir(reflection_dir)
            reflection_meta = {
                "description": reflection.description,
                "source_table": reflection.source_table.pk,
                "destination_database": reflection.destination_database.pk,
                "destination_table": reflection.destination_table,
                "last_commit": reflection.last_commit,
                # "last_updated": reflection.last_updated,
                "active": reflection.active,
                "ignore_delete_events": reflection.ignore_delete_events
            }
            source_fields = json.loads(reflection.source_fields)
            destination_fields = json.loads(reflection.destination_fields)
            reflection_statment = reflection.reflection_statment
            with open(os.path.join(reflection_dir, "meta.json"), "w") as file:
                file.write(json.dumps(reflection_meta, indent=4))
            with open(
                    os.path.join(
                        reflection_dir,
                        "source_fields.json"
                    ), "w") as file:
                file.write(json.dumps(source_fields, indent=4))
            with open(
                    os.path.join(
                        reflection_dir,
                        "destination_fields.json"
                    ), "w") as file:
                file.write(json.dumps(destination_fields, indent=4))
            with open(
                    os.path.join(
                        reflection_dir,
                        "reflection_statment.sql"
                    ), "w") as file:
                file.write(reflection_statment)
