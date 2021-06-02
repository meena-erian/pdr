from django.core.management.base import BaseCommand, CommandError
from django_pdr.models import Reflection
import logging
import time


logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Update all destincation database by any '\
        'pending changes in source tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--interval',
            type=int,
            help='Indicates the number seconds delay between each '
            'reflection cycle. By default it reflects only once'
        )
        parser.add_argument(
            '-l',
            '--log',
            type=int,
            help='Logging level. (0-5, NOTSET-CRITICAL) default is 3'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        log = options['log']
        if isinstance(log, int):
            log = log * 10
            logging.info("Setting log level to {0}".format(log))
            logging.getLogger('root').setLevel(log)
        try:
            while True:
                for reflection in Reflection.objects.all():
                    if reflection.active:
                        logging.info(
                            str(reflection)
                            + ': '
                            + str(reflection.reflect())
                        )
                if interval:
                    time.sleep(interval)
                else:
                    break
        except KeyboardInterrupt:
            logging.warning('Terminating PDR worker')
