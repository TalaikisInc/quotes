from django.core.management.base import BaseCommand

from tasks.utils import retitle, rewriter, clean_empty_cats, correct_cat_titles


class Command(BaseCommand):
    help = 'Temporary utils to transition from old db to new PGV db model'

    def handle(self, *args, **options):
        #retitle()
        #rewriter()
        #clean_empty_cats()
        correct_cat_titles()

        self.stdout.write(self.style.SUCCESS('Successfully done jobs'))
