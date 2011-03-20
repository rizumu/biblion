# -*- coding: utf8 -*-
import urllib2

from datetime import datetime

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from django.contrib.sites.models import Site

try:
    import twitter
except ImportError:
    twitter = None

from biblion.managers import PostManager
from biblion.settings import ALL_SECTION_NAME, SECTIONS
from biblion.utils import can_tweet



def ig(L, i):
    for x in L:
        yield x[i]


class Post(models.Model):
    
    SECTION_CHOICES = [(1, ALL_SECTION_NAME)] + zip(range(2, 2 + len(SECTIONS)), ig(SECTIONS, 1))
    
    section = models.IntegerField(_("section"), choices=SECTION_CHOICES)
    
    title = models.CharField(_("title"), max_length=90)
    slug = models.SlugField()
    author = models.ForeignKey(User, related_name="posts", verbose_name=_('author'))
    
    teaser_html = models.TextFi ld(_("teaser html"), editable=False)
    content_html = models.TextFie d(_("content html"), editable=False)
    
    tweet_text = models.CharField(_("tweet text"), max_length=140, editable=False)
    
    created = models.DateTimeField(_("created"), default=datetime.now, editable=False) # when first revision was created
    updated = models.DateTimeField(_("updated"), null=True, blank=True, editable=False) # when last revision was create (even if not published)
    published = models.DateTimeField(_("published"), null=True, blank=True, editable=False) # when last published
    
    view_count = models.IntegerField(_("view count"), default=0, editable=False)
    
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
        "the currently visible (latest published) revision"
        return self.revisions.exclude(published=None).order_by("-published")[0]
    
    def latest(self):
        "the latest modified (even if not published) revision"
        try:
            return self.revisions.order_by("-updated")[0]
        except IndexError:
            return None
    
    class Meta:
        get_latest_by = "published"
        ordering = ("-published",)
        verbose_name = _("post")
        verbose_name_plural = _("posts")
    
    objects = PostManager()
    
    def __unicode__(self):
        return self.title
    
    def as_tweet(self):
        if not self.tweet_text:
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
                username = settings.TWITTER_USERNAME,
                password = settings.TWITTER_PASSWORD,
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
            name = "blog_post_pk"
            kwargs = {
                "post_pk": self.pk,
            }
        return reverse(name, kwargs=kwargs)
    
    def inc_views(self):
        self.view_count += 1
        self.save()
        self.current().inc_views()


class Revision(models.Model):
    
    post = models.ForeignKey(Post, related_name="revisions", verbose_name=_('post'))
    
    title = models.CharField(_("title"), max_length=90)
    teaser = models.TextField(_("teaser"), )
    
    content = models.TextField(_("content"), )
    
    author = models.ForeignKey(User, related_name="revisions", verbose_name=_('author'))
    
    updated = models.DateTimeField(_("updated"), default=datetime.now)
    published = models.DateTimeField(_("published"), null=True, blank=True)
    
    view_count = models.IntegerField(_("view count"), default=0, editable=False)
    
    def __unicode__(self):
        return 'Revision %s for %s' % (self.updated.strftime('%Y%m%d-%H%M'), self.post.slug)

    class Meta:
        verbose_name = _("revision")
        verbose_name_plural = _("revisions")
    
    def inc_views(self):
        self.view_count += 1
        self.save()


class Image(models.Model):
    
    post = models.ForeignKey(Post, related_name="images", verbose_name=_('post'))
    
    image_path = models.ImageField(_("image path"), upload_to="images/%Y/%m/%d")
    url = models.CharField(_("url"), max_length=150, blank=True)
    
    timestamp = models.DateTimeField(_("timestamp"), default=datetime.now, editable=False)
    
    class Meta:
        verbose_name = _("image")
        verbose_name_plural = _("images")


    def __unicode__(self):
        if self.pk is not None:
            return "{{ %d }}" % self.pk
        else:
            return "deleted image"

class FeedHit(models.Model):
    
    request_data = models.TextField(_("request data"))
    created = models.DateTimeField(_("created"), default=datetime.now)

    class Meta:
        verbose_name = _("feed hit")
        verbose_name_plural = _("feed hits")
