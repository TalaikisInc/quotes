from django.db import transaction

from .models import Post, Category


@transaction.atomic
def retitle():
    posts = Post.objects.filter(slug=None)
    print(posts.count())

    for post in posts:
        post.title = post.title
        post.save()
        print(post.slug)


def rewriter():
    posts = Post.objects.filter(content__icontains="<br/>")

    for post in posts:
        text = post.content.replace("<br/>", "<br /><br />")
        post.content = text
        post.save()
    
    posts = Post.objects.filter(content__icontains="Quote:")

    for post in posts:
        text = post.content.replace("Quote: ", "")
        post.content = text
        post.save()


def clean_empty_cats():
    cats = Category.objects.filter(title=" ").delete()


def correct_cat_titles():
    cats = Category.objects.all()
    for cat in cats:
        if cat.title[0] == " ":
            try:
                cat.title = cat.title[1:]
                cat.save()
            except:
                existing_cat = Category.objects.get(title=cat.title)
                posts = Post.objects.filter(category=cat)
                for post in posts:
                    post.category = existing_cat
                    post.save()
                cat.delete()
