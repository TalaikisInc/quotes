from django.db import models
from django.utils.translation import ugettext as T
from django.db import IntegrityError
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags


class AutoSlugifyOnSaveModel(models.Model):
    """
    http://www.laurencegellert.com/2016/04/django-automatic-slug-generator/
    Models that inherit from this class get an auto filled slug property based on the models name property.
    Correctly handles duplicate values (slugs are unique), and truncates slug if value too long.
    The following attributes can be overridden on a per model basis:
    * value_field_name - the value to slugify, default 'name'
    * slug_field_name - the field to store the slugified value in, default 'slug'
    * max_interations - how many iterations to search for an open slug before raising IntegrityError, default 1000
    * slug_separator - the character to put in place of spaces and other non url friendly characters, default '-'
    """

    def save(self, *args, **kwargs):
        pk_field_name = self._meta.pk.name
        value_field_name = getattr(self, 'value_field_name', 'title')
        slug_field_name = getattr(self, 'slug_field_name', 'slug')
        max_interations = getattr(self, 'slug_max_iterations', 1000)
        slug_separator = getattr(self, 'slug_separator', '-')

        # fields, query set, other setup variables
        slug_field = self._meta.get_field(slug_field_name)
        slug_len = slug_field.max_length
        queryset = self.__class__.objects.all()

        # if the pk of the record is set, exclude it from the slug search
        current_pk = getattr(self, pk_field_name)

        if current_pk:
            queryset = queryset.exclude(**{pk_field_name: current_pk})

        # setup the original slug, and make sure it is within the allowed length
        slug = slugify(getattr(self, value_field_name)).replace('-', '_')

        if slug_len:
            slug = slug[:slug_len]

        original_slug = slug

        # iterate until a unique slug is found, or max_iterations
        counter = 2
        while queryset.filter(**{slug_field_name: slug}).count() > 0 and counter < max_interations:
            slug = original_slug
            suffix = '%s%s' % (slug_separator, counter)
            if slug_len and len(slug) + len(suffix) > slug_len:
                slug = slug[:slug_len-len(suffix)]
            slug = '%s%s' % (slug, suffix)
            counter += 1

        if counter == max_interations:
            raise IntegrityError('Unable to locate unique slug')

        setattr(self, slug_field.attname, slug)

        super(AutoSlugifyOnSaveModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Category(AutoSlugifyOnSaveModel):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=120, verbose_name=T("Categoery"), db_index=True, unique=True)
    slug = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        ordering = ('title',)

    def __unicode__(self):
        return '%s' %(self.title)

    def __str__(self):
        return '%s' %(self.title)


class Tag(AutoSlugifyOnSaveModel):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150, verbose_name=T("Tag"), unique=True)
    slug = models.CharField(max_length=150, blank=True, null=True)

    def __unicode__(self):
        return '%s' %(self.title)

    def __str__(self):
        return '%s' %(self.title)


class Post(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=T("Categoery"))
    content = models.TextField(verbose_name=T("Content"))
    image = models.ImageField(upload_to="uploads/", blank=True, null=True, verbose_name=T("Image"))
    tags = models.ManyToManyField(Tag, blank=True, verbose_name=T("Tags"))

    def save(self, *args, **kwargs):
        self.title = strip_tags(self.content[:80])
        super(Post, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s' %(self.title)

    def __str__(self):
        return '%s' %(self.title)


class Links(models.Model):
    LINK_STATUSES = (
        (0, 'Unknown'),
        (1, 'Term link'),
        (2, 'Article in db'),
    )

    url = models.URLField(verbose_name=T("URL to topic"), primary_key=True)
    status_parsed = models.SmallIntegerField(verbose_name=T("Parse status"), choices=LINK_STATUSES, default=0)

    def __unicode__(self):
        return '%s' %(self.url)

    def __str__(self):
        return '%s' %(self.url)