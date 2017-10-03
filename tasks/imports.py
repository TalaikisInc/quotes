from os.path import join

from pandas import read_csv
from clint.textui import colored

from django.conf import settings

from .models import Tag, Post, Category


def read_quotes_csv():
	path_to = join(settings.BASE_DIR, "data", "quotes.csv")

	df = read_csv(filepath_or_buffer=path_to, sep=',', delimiter=None, \
		header=0, names=None, index_col=None, usecols=None, squeeze=False, prefix=None, \
        mangle_dupe_cols=True, dtype=None, engine=None, \
		converters=None, true_values=None, false_values=None, \
		skipinitialspace=False, skiprows=None, nrows=None, \
		na_values=None, keep_default_na=True, na_filter=True, \
		verbose=False, skip_blank_lines=True, parse_dates=False, \
		infer_datetime_format=False, keep_date_col=False, \
		date_parser=None, dayfirst=False, iterator=False, chunksize=None, \
		compression='infer', thousands=None, decimal='.', lineterminator=None, \
		quotechar='"', quoting=0, escapechar=None, comment=None, \
		encoding=None, dialect=None, tupleize_cols=False, \
		error_bad_lines=True, warn_bad_lines=True, skipfooter=0, \
		skip_footer=0, doublequote=True, delim_whitespace=False, \
		as_recarray=False, compact_ints=False, use_unsigned=False, \
		low_memory=False, buffer_lines=None, memory_map=False, \
		float_precision=None)
	return df


def get_tag(tag_data):
	try:
		tag = Tag.objects.get(title=tag_data)
	except:
		tag = Tag.objects.create(title=tag_data)

	return tag


def get_author(author_data):
	try:
		author = Category.objects.get(title=author_data)
	except:
		author = Category.objects.create(title=author_data)

	return author


def csv_to_db():
    df = read_quotes_csv()

    for i in range(len(df)):
        quote_data = df.ix[i].QUOTE
        author_data = df.ix[i].AUTHOR
        tag_data = df.ix[i].GENRE
	
        tag = get_tag(tag_data=tag_data)
        author = get_author(author_data=author_data)

        try:
            quote = Post.objects.create(content=quote_data, category=author)
            quote.tags.add(tag)
            quote.save()
            print("Quote: {} inserted".format(quote_data))
        except Exception as err:
            print(colored.red("At csv_to_db {}".format(err)))