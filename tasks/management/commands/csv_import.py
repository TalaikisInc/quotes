from django.core.management.base import BaseCommand

from tasks.imports import csv_to_db


class Command(BaseCommand):
    help = 'CSV to db quotes importer..'

    def handle(self, *args, **options):
        csv_to_db()

        self.stdout.write(self.style.SUCCESS('Successfully done jobs'))
