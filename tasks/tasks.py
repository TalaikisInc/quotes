from os.path import join
import re
from random import choice, shuffle
from asyncio import gather

from bs4 import BeautifulSoup
import requests
from clint.textui import colored
from nltk.tokenize import sent_tokenize

from django.db import IntegrityError
from django.conf import settings
from django.utils.encoding import smart_text

from .models import Post, Category, Tag, Links


def load_user_agents(uafile=join(settings.BASE_DIR, 'user_agents.txt')):
    uas = []
    with open(uafile, 'r') as uaf:
        for ua in uaf.readlines():
            if ua:
                uas.append(ua.strip()[1:-1-1])
    shuffle(uas)
    return uas


HEADERS = {
    "Connection" : "close",
    'User-Agent': choice(load_user_agents())
}

PROXIES_LIST = ['5.2.72.57:3128', '203.74.4.6:80', '205.189.37.79:53281', '47.91.165.126:8088']
SSL_PROXIES = []

PROXIES = {
    'http': choice(PROXIES_LIST),
    'https': ''#random.choice(SSL_PROXIES),
}


def match_class(target):                                                        
    def do_match(tag):                                                          
        classes = tag.get('class', [])                                          
        return all(c in classes for c in target)                                
    return do_match  


async def link_collector(what, source, initial, link_type, base_link):
    try:
        if source.status_code == 200:
            tree = BeautifulSoup(source.text, 'html.parser')

            a = tree.find_all('a')
            if not a is None:
                for l in a:
                    link = l.get('href')
                    if not "?" in link:
                        if any([w for w in what if w in link]):
                            try:
                                if not ('http://' or 'https://') in link:
                                    link = "{0}{1}".format(base_link, link)
                                    entry = Links.objects.create(url=link, status_parsed=0)
                                else:
                                    entry = Links.objects.create(url=link, status_parsed=0)
                                entry.save()
                                print(colored.green("Saved link."))
                            except IntegrityError:
                                pass
    except Exception as err:
        print(colored.red("Failed at collector: {0}".format(err)))


def get_article(link_, original_link):
    try:
        if not ('page' in link_):
            article = get_body_from_internet(link_)
            if 'Definition' in article.title:
                entry = Terms.objects.create(term=article.title, text=article.text, \
                        movies=article.movies, image=article.top_image)
                entry.save()
                print("Article saved in db.")
                update_link(original_link, 'A')
            else:
                update_link(original_link, 'A')
        else:
            update_link(original_link, 'A')
    except IntegrityError as e:
        print(e)
        update_link(original_link, 'A')


async def save_quote(author: str, quote: str):
    """
    Saves quote.
    """
    try:
        a = Category.objects.get(title=author)
    except Exception as err:
        print(colored.red(err))
        a = Category.objects.create(title=author)

    try:
        q = Post.objects.create(quote=quote, author=a)
    except Exception as err:
        print(colored.red(err))


async def get_quotes(link, info, base_url, p=False):
    """
    Processes each quote.
    """
    if p:
        s = requests.get(link, headers=HEADERS, proxies=PROXIES)
    else:
        s = requests.get(link, headers=HEADERS)
    if s.status_code == 200:
        tree = BeautifulSoup(s.text, 'html.parser')

        if info["main_link"] == base_url:
            quot = tree.find_all(match_class(["edit_body"]))
            auth = tree.find_all(match_class(["authors"]))

            quote = str(quot[0]).split('>"')[1].split('"<')[0]
            author = str(auth[0]).split("</a>")[0].split('">')[-1]

            await save_quote(author=author, quote=quote)


async def get_each(i, info, base_url):
    if info["main_link"] == base_url:
        print(i)
        link = "{0}/quote/{1}".format(info["main_link"], i)
        await get_quotes(link=link, info=info, base_url=base_url)


def parse_quotes(loop, info, base_url):
    """
    Main fucntion.
    """
    if info["main_link"] == base_url:
        for p in range(2200, 2219):
            loop.run_until_complete(gather(*[get_each(i=i, info=info, base_url=base_url) \
                for i in range(p*1000, (p+1)*1000)], return_exceptions=True))


async def process_links(what, source, base_link):
    try:
        if ('http://' or 'https://') in source.url:
            s = requests.get(source.url)
            await link_collector(what=what, source=s, initial=source.url, link_type=0, base_link=base_link)
        else:
            link = "{0}{1}".format(base_link, source.url)
            s = requests.get(link)
            await link_collector(what=what, source=s, initial=source.url, link_type=0, base_link=base_link)
    except Exception as err:
        print(colored.red("Failed at parsing db links: {0}".format(err)))


def init(loop, what, main_link, base_link, iterations):
    if Links.objects.count() == 0:
        source = requests.get(main_link, headers=HEADERS)
        if source.status_code == 200:
            tree = BeautifulSoup(source.text, 'html.parser')

            for l in tree.find_all('a'):
                link = l.get('href')
                try:
                    if not "?" in link:
                        if any([w for w in what if w in link]):
                            entry = Links.objects.create(url=link, status_parsed=0)
                            entry.save()
                            print(colored.green("Saved link."))
                except IntegrityError:
                    pass
                except Exception as err:
                    print(i)
                    print(colored.red("Failed at initial parse: {}".format(err)))
    else:
        for i in range(iterations):
            sources = Links.objects.filter(status_parsed=0)

            loop.run_until_complete(gather(*[process_links(what=what, source=source, base_link=base_link) \
                for source in sources], return_exceptions=True))
