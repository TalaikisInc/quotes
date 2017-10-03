from asyncio import get_event_loop

from django.core.management.base import BaseCommand

from tasks.tasks import posts_wordcloud


class Command(BaseCommand):
    help = 'Parses feeds and exewcutes additional cleaning.'

    def handle(self, *args, **options):
        loop = get_event_loop()

        posts_wordcloud(loop=loop)

        loop.close()

        self.stdout.write(self.style.SUCCESS('Successfully generated wordclouds.'))