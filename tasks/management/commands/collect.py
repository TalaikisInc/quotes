from asyncio import get_event_loop

from django.core.management.base import BaseCommand
from django.conf import settings

from tasks.tasks import init, parse_quotes


class Command(BaseCommand):
    help = 'Quotes parser.'

    def handle(self, *args, **options):
        list_of_sites = [
                {"what": ["quotes/"], "main_link": settings.PARSE_URL, "base_link": settings.PARSE_URL},
            ]
        iterations = 1

        loop = get_event_loop()

        init(loop=loop, what=what, main_link=main_link, base_link=list_of_sites[0]["main_link"], iterations=iterations)
        for site in list_of_sites:
            parse_quotes(loop=loop, info=site, base_url=site["main_link"])

        loop.close()

        self.stdout.write(self.style.SUCCESS('Successfully done parsing jobs'))
