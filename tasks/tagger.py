from asyncio import gather
from operator import itemgetter
from sys import version
from re import UNICODE, findall
from collections import defaultdict
from math import log

from django.core.exceptions import ObjectDoesNotExist
from nltk.corpus import stopwords
from nltk import pos_tag
from nltk.tokenize import word_tokenize

from django.utils.html import strip_tags

from .models import Post, Tag


"""
Below code is modified version pf (c) https://github.com/amueller/word_cloud
"""

def dunning_likelihood(k, n, x):
    # dunning's likelihood ratio with notation from
    # http://nlp.stanford.edu/fsnlp/promo/colloc.pdf p162
    return log(max(x, 1e-10)) * k + log(max(1 - x, 1e-10)) * (n - k)


def score(count_bigram, count1, count2, n_words):
    """Collocation score"""
    if n_words <= count1 or n_words <= count2:
        # only one words appears in the whole document
        return 0
    N = n_words
    c12 = count_bigram
    c1 = count1
    c2 = count2
    p = c2 / N
    p1 = c12 / c1
    p2 = (c2 - c12) / (N - c1)
    score = (dunning_likelihood(c12, c1, p) + dunning_likelihood(c2 - c12, N - c1, p)
             - dunning_likelihood(c12, c1, p1) - dunning_likelihood(c2 - c12, N - c1, p2))
    return -2 * score


def pairwise(iterable):
    from itertools import tee

    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def process_tokens(words, normalize_plurals=True):
    d = defaultdict(dict)
    for word in words:
        word_lower = word.lower()
        # get dict of cases for word_lower
        case_dict = d[word_lower]
        # increase this case
        case_dict[word] = case_dict.get(word, 0) + 1
    if normalize_plurals:
        # merge plurals into the singular count (simple cases only)
        merged_plurals = {}
        for key in list(d.keys()):
            if key.endswith('s') and not key.endswith("ss"):
                key_singular = key[:-1]
                if key_singular in d:
                    dict_plural = d[key]
                    dict_singular = d[key_singular]
                    for word, count in dict_plural.items():
                        singular = word[:-1]
                        dict_singular[singular] = (
                            dict_singular.get(singular, 0) + count)
                    merged_plurals[key] = key_singular
                    del d[key]
    fused_cases = {}
    standard_cases = {}
    item1 = itemgetter(1)
    for word_lower, case_dict in d.items():
        # Get the most popular case.
        first = max(case_dict.items(), key=item1)[0]
        fused_cases[first] = sum(case_dict.values())
        standard_cases[word_lower] = first
    if normalize_plurals:
        # add plurals to fused cases:
        for plural, singular in merged_plurals.items():
            standard_cases[plural] = standard_cases[singular.lower()]
    return fused_cases, standard_cases


def unigrams_and_bigrams(words, normalize_plurals=True):
    n_words = len(words)
    # make tuples of two words following each other
    bigrams = list(pairwise(words))
    counts_unigrams = defaultdict(int)
    counts_bigrams = defaultdict(int)
    counts_unigrams, standard_form = process_tokens(
        words, normalize_plurals=normalize_plurals)
    counts_bigrams, standard_form_bigrams = process_tokens(
        [" ".join(bigram) for bigram in bigrams],
        normalize_plurals=normalize_plurals)
    # create a copy of counts_unigram so the score computation is not changed
    counts = counts_unigrams.copy()

    # decount words inside bigrams
    for bigram_string, count in counts_bigrams.items():
        bigram = tuple(bigram_string.split(" "))
        # collocation detection (30 is arbitrary):
        word1 = standard_form[bigram[0].lower()]
        word2 = standard_form[bigram[1].lower()]

        if score(count, counts[word1], counts[word2], n_words) > 30:
            # bigram is a collocation
            # discount words in unigrams dict. hack because one word might
            # appear in multiple collocations at the same time
            # (leading to negative counts)
            counts_unigrams[word1] -= counts_bigrams[bigram_string]
            counts_unigrams[word2] -= counts_bigrams[bigram_string]
            counts_unigrams[bigram_string] = counts_bigrams[bigram_string]
    words = list(counts_unigrams.keys())
    for word in words:
        # remove empty / negative counts
        if counts_unigrams[word] <= 0:
            del counts_unigrams[word]
    return counts_unigrams


class WordCloudMod(object):
    def __init__(self, max_words=200, relative_scaling=.5, regexp=None, collocations=True,
                 colormap=None, normalize_plurals=True):
        self.collocations = collocations
        self.max_words = max_words
        self.regexp = regexp
        self.normalize_plurals = normalize_plurals
        self.item1 = itemgetter(1)

    def fit_words(self, frequencies):
        return self.generate_from_frequencies(frequencies)

    def generate_from_frequencies(self, frequencies):
        # make sure frequencies are sorted and normalized
        frequencies = sorted(frequencies.items(), key=self.item1, reverse=True)
        if len(frequencies) <= 0:
            raise ValueError("We need at least 1 word to plot a word cloud, "
                             "got %d." % len(frequencies))
        frequencies = frequencies[:self.max_words]

        # largest entry will be 1
        max_frequency = float(frequencies[0][1])

        frequencies = [(word, freq / max_frequency)
                       for word, freq in frequencies]
        
        self.words_ = dict(frequencies)

        return self.words_

    def process_text(self, text):
        flags = (UNICODE if version < '3' and type(text) is unicode
                 else 0)
        regexp = self.regexp if self.regexp is not None else r"\w[\w']+"

        words = findall(regexp, text, flags)
        # remove stopwords
        words = [word for word in words]
        # remove 's
        words = [word[:-2] if word.lower().endswith("'s") else word
                 for word in words]
        # remove numbers
        words = [word for word in words if not word.isdigit()]

        if self.collocations:
            word_counts = unigrams_and_bigrams(words, self.normalize_plurals)
        else:
            word_counts, _ = process_tokens(words, self.normalize_plurals)

        return word_counts

    def generate_from_text(self, text):
        words = self.process_text(text)
        freqs = self.generate_from_frequencies(words)
        return freqs

    def generate(self, text):
        return self.generate_from_text(text)


def filter_insignificant(chunk, tag_suffixes=['DT', 'CC', 'CD', 'POS', 'PRP']):
    good = []

    for word, tag in chunk:
        ok = True

        for suffix in tag_suffixes:
            if tag.endswith(suffix):
                ok = False
                break

        if ok:
            good.append(word)

    return good


def words_wo_stopwords(text):
    """
    Cleans text from stop words.
    """
    nltk_stopwords_list = stopwords.words('english')

    stopwords_list = list(set(nltk_stopwords_list + ["'s", "n't"]))

    words = word_tokenize(strip_tags(text))
    cleaned = [w for w in words if not w.lower() in stopwords_list]
    text = " ".join(cleaned)

    return text


async def keyword_extractor(data: str) -> list:
    try:
        text = words_wo_stopwords(strip_tags(data))

        words = word_tokenize(strip_tags(text))
        taggged = pos_tag(words)
        cleaned = filter_insignificant(taggged)
        text = " ".join(cleaned)
        wc = WordCloudMod().generate(text)
        result = list(wc.keys())[:10]
    except Exception as err:
        print(colored.red("At keywords extraction {}".format(err)))
        result = []

    return result


async def save_tags(tags, entry):
    try:
        if len(tags) > 0:
            for tag in tags:
                if "'s" not in tag:
                    try:
                        tag_obj = Tags.objects.get(title=tag)
                    except ObjectDoesNotExist:
                        tag_obj = Tags.bjects.create(title=tag)
                        tag_obj.save()
                        print(colored.green("Added tag '{0}' to entry".format(tag)))
                    entry.tags.add(tag_obj)
    except IntegrityError:
        pass
    except Exception as err:
        print(colored.red("At save_tags {}".format(err)))
    
    return entry


async def keyword_process(post):
    try:
        tags = await keyword_extractor(data=post.quote)
        await save_tags(tags=tags, entry=post)
    except Exception as err:
        print(colored.red("keyword_process {}".format(err)))


def posts_wordcloud(loop):
    """
    Generates wordcloud foeach post.
    """
    posts = Post.objects.all()

    loop.run_until_complete(gather(*[keyword_process(post=post) \
        for post in posts], return_exceptions=True))
