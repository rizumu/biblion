# -*- coding: utf-8 -*-
import urllib2

from datetime import datetime

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site

try:
    import twitter
except ImportError:
    twitter = None
try:
    from licenses.fields import LicenseField
except ImportError:
    LicenseField = None

if "taggit" in settings.INSTALLED_APPS:
    from taggit.managers import TaggableManager
else:
    def TaggableManager():
        return None

from biblion.managers import BlogManager, PostManager
from biblion.settings import ALL_SECTION_NAME, SECTIONS
from biblion.utils.db import manager_from
from biblion.utils.twitter import can_tweet
from biblion.utils.fields import UUIDField


class Blog(models.Model):
    
    uuid = UUIDField(_("id"), unique=True)
    
    site = models.ForeignKey(
        Site, related_name=("blogs"), default=settings.SITE_ID, verbose_name=_("site"))
    
    title = models.CharField(_("title"), max_length=90)
    slug = models.SlugField()
    maintainers = models.ManyToManyField(
        User, related_name=_("blog_maintainers"), verbose_name=_("maintainers"), null=True, blank=True)
    
    subtitle = models.CharField(
        _("subtitle"), max_length=255, blank=True, help_text="Looks best if only a few words, like a tagline.")
    description = models.TextField(_("description"), max_length=4000, help_text=_("""
        This is your chance to tell potential subscribers all about your blog.
        Describe your subject matter, media format, post schedule, and other
        relevant info so that they know what they'll be getting when they
        subscribe. In addition, make a list of the most relevant search terms
        that you want your blog to match, then build them into your
        description. This field can be up to 4000 characters."""), blank=True)
    
    feedburner = models.URLField(_("feedburner url"), blank=True,
        help_text=_("""Fill this out after saving this show and at least one
        episode. URL should look like "http://feeds.feedburner.com/TitleOfShow".
        <a href="http://www.feedburner.com/fb/a/ping">Manually ping</a>"""))
    
    if LicenseField:
        license = LicenseField(related_name=_("blogs"))
    
    authors = models.ManyToManyField(
        User, related_name=_("blog_authors"), verbose_name=_("authors"), null=True, blank=True)
    contributors = models.ManyToManyField(
        User, related_name=_("blog_contributors"), verbose_name=_("contributors"), null=True, blank=True)
    
    posts_per_page = models.PositiveIntegerField(_("posts per page"), default=6)
    
    created = models.DateTimeField(_("created"), default=datetime.now, editable=False)
    updated = models.DateTimeField(_("updated"), null=True, blank=True, editable=False)
    published = models.DateTimeField(_("published"), null=True, blank=True, editable=False)  # when last published
    
    objects = manager_from(BlogManager)
    on_site = CurrentSiteManager()
    tags = TaggableManager()
    
    class Meta:
        ordering = ("site", "title")
        unique_together = ("title", "site")
        verbose_name = _("blog")
        verbose_name_plural = _("blogs")
    
    def __unicode__(self):
        return u"%s" % (self.title)
    
    def get_absolute_url(self):
        return reverse("blog_detail", kwargs={"blog_slug": self.slug})


def ig(L, i):
    for x in L:
        yield x[i]


class Post(models.Model):
    
    uuid = UUIDField(_("id"), unique=True)
    
    blog = models.ForeignKey(Blog, related_name=_("posts"))
    
    SECTION_CHOICES = [(1, ALL_SECTION_NAME)] + zip(range(2, 2 + len(SECTIONS)), ig(SECTIONS, 1))
    markup_types = ["HTML", "Creole", "Markdown", "reStructuredText", "Textile"]
    MARKUP_CHOICES = zip(range(1, 1 + len(markup_types)), markup_types)
    markup_type = models.IntegerField(choices=MARKUP_CHOICES, default=1)
    
    section = models.IntegerField(_("section"), choices=SECTION_CHOICES)
    
    title = models.CharField(_("title"), max_length=90)
    slug = models.SlugField()
    
    authors = models.ManyToManyField(
        User, related_name=_("post_authors"), verbose_name=_("authors"), null=True, blank=True)
    contributors = models.ManyToManyField(
        User, related_name=_("post_contributors"), verbose_name=_("contributors"), null=True, blank=True)
    
    teaser = models.TextField(_("teaser"), editable=False)
    content = models.TextField(_("content"), editable=False)
    
    tweet_text = models.CharField(_("tweet text"), max_length=140, editable=False)
    
    if LicenseField:
        license = LicenseField(related_name=_("posts"))
    
    created = models.DateTimeField(
        _("created"), default=datetime.now, editable=False)  # when first revision was created
    updated = models.DateTimeField(
        _("updated"), null=True, blank=True, editable=False)  # when last revision was create (even if not published)
    published = models.DateTimeField(
        _("published"), null=True, blank=True, editable=False)  # when last published
    
    view_count = models.IntegerField(_("view count"), default=0, editable=False)
    comments = models.BooleanField(_("comments"), default=True)
    
    objects = manager_from(PostManager)
    tags = TaggableManager()
    
    class Meta:
        get_latest_by = "published"
        ordering = ("-published",)
        verbose_name = _("post")
        verbose_name_plural = _("posts")
    
    def __unicode__(self):
        return u"%s" % (self.title)
    
    @staticmethod
    def section_idx(slug):
        """
        given a slug return the index for it
        """
        if slug == ALL_SECTION_NAME:
            return 1
        return dict(zip(ig(SECTIONS, 0), range(2, 2 + len(SECTIONS))))[slug]
    
    @property
    def section_slug(self):
        """
        an IntegerField is used for storing sections in the database so we
        need a property to turn them back into their slug form
        """
        if self.section == 1:
            return ALL_SECTION_NAME
        return dict(zip(range(2, 2 + len(SECTIONS)), ig(SECTIONS, 0)))[self.section]
    
    def rev(self, rev_id):
        return self.revisions.get(pk=rev_id)
    
    def current(self):
        """
        the currently visible (latest published) revision
        """
        return self.revisions.exclude(published=None).latest("published")
    
    def latest(self):
        """
        the latest modified (even if not published) revision
        """
        try:
            return self.revisions.latest("updated")
        except ObjectDoesNotExist:
            return None
    
    def as_tweet(self):
        if not self.tweet_text:
            if self.blog.site:
                current_site = self.blog.site
            else:
                current_site = Site.objects.get_current()
            api_url = "http://api.tr.im/api/trim_url.json"
            u = urllib2.urlopen("%s?url=http://%s%s" % (
                api_url,
                current_site.domain,
                self.get_absolute_url(),
            ))
            result = json.loads(u.read())
            self.tweet_text = u"%s %s — %s" % (
                settings.TWITTER_TWEET_PREFIX,
                self.title,
                result["url"],
            )
        return self.tweet_text
    
    def tweet(self):
        if can_tweet():
            account = twitter.Api(
                username=settings.TWITTER_USERNAME,
                password=settings.TWITTER_PASSWORD,
            )
            account.PostUpdate(self.as_tweet())
        else:
            raise ImproperlyConfigured("Unable to send tweet due to either "
                                       "missing python-twitter or required settings.")
    
    def save(self, **kwargs):
        self.updated_at = datetime.now()
        super(Post, self).save(**kwargs)
    
    def get_absolute_url(self):
        if self.published:
            name = "blog_post"
            kwargs = {
                "year": self.published.strftime("%Y"),
                "month": self.published.strftime("%m"),
                "day": self.published.strftime("%d"),
                "slug": self.slug,
            }
        else:
            name = "blog_post_uuid"
            kwargs = {
                "post_uuid": self.uuid,
            }
        kwargs["blog_slug"] = self.blog.slug
        return reverse(name, kwargs=kwargs)
    
    def inc_views(self):
        self.view_count += 1
        self.save()
        self.current().inc_views()


class Revision(models.Model):
    
    post = models.ForeignKey(Post, related_name="revisions", verbose_name=_("post"))
    
    title = models.CharField(_("title"), max_length=90)
    teaser = models.TextField(_("teaser"), )
    
    content = models.TextField(_("content"), )
    
    authors = models.ManyToManyField(
        User, related_name="revisions_authors", verbose_name=_("authors"), null=True, blank=True)
    contributors = models.ManyToManyField(
        User, related_name="revisions_contributors", verbose_name=_("authors"), null=True, blank=True)
    
    updated = models.DateTimeField(_("updated"), default=datetime.now)
    published = models.DateTimeField(_("published"), null=True, blank=True)
    
    view_count = models.IntegerField(_("view count"), default=0, editable=False)
    
    class Meta:
        verbose_name = _("revision")
        verbose_name_plural = _("revisions")
    
    def __unicode__(self):
        return u"Revision %s for %s" % (self.updated.strftime("%Y%m%d-%H%M"), self.post.slug)
    
    def inc_views(self):
        self.view_count += 1
        self.save()


class Image(models.Model):
    
    post = models.ForeignKey(Post, related_name="images", verbose_name=_("post"))
    
    image_path = models.ImageField(_("image path"), upload_to="images/%Y/%m/%d")
    url = models.CharField(_("url"), max_length=150, blank=True)
    
    timestamp = models.DateTimeField(_("timestamp"), default=datetime.now, editable=False)
    
    class Meta:
        verbose_name = _("image")
        verbose_name_plural = _("images")
    
    def __unicode__(self):
        if self.pk is not None:
            return u"{{ %d }}" % self.pk
        else:
            return u"deleted image"


class FeedHit(models.Model):
    
    request_data = models.TextField(_("request data"))
    created = models.DateTimeField(_("created"), default=datetime.now)
    
    class Meta:
        verbose_name = _("feed hit")
        verbose_name_plural = _("feed hits")
