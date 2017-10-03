from django.contrib import admin

from .models import Links, Post, Category, Tag


admin.site.register(Links)
admin.site.register(Tag)
admin.site.register(Post)
admin.site.register(Category)