import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from django.utils import simplejson as json

from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed

from biblion.models import Blog, Post, FeedHit


def serialize_request(request):
    data = {
        "path": request.path,
        "META": {
            "QUERY_STRING": request.META.get("QUERY_STRING"),
            "REMOTE_ADDR": request.META.get("REMOTE_ADDR"),
        }
    }
    for key in request.META:
        if key.startswith("HTTP"):
            data["META"][key] = request.META[key]
    return json.dumps(data)


class LatestPostBaseFeed(Feed):
    """
    Base Feed of the latest 10 posts.
    """
    def get_object(self, request, blog_slug, site=Site.objects.get_current()):
        if request:
            # Create a feed hit.
            # Is this really necessary? How about a signal instead?
            hit = FeedHit()
            hit.request_data = serialize_request(request)
            hit.save()
        return get_object_or_404(Blog, slug=blog_slug, site=site)
    
    def items(self, obj):
        return Post.objects.published().filter(blog=obj)[:10]
    
    def title(self, obj):
        return "%s feed" % obj
    
    def updated(self, obj):
        latest_post = Post.objects.filter(blog=obj).latest()
        return latest_post.published
    
    def link(self, obj):
        # TODO: support hreflang
        return reverse("blog_detail", args=[obj.slug])
    
    def description(self, obj):
        return obj.subtitle
    
    def generator(self):
        return "Django Web Framework"
    
    def guid(self, obj):
        return obj.pk
    
    def copyright(self, obj):
        return "{0} {1} {2}".format(obj.license.name, obj.license.url,
            datetime.date.today().year)
    
    def author_name(self, obj):
        return obj.authors.all()[0].get_full_name()
    
    def author_email(self, obj):
        return obj.authors.all()[0].email

    # TODO: Support the following `feed` tags
    def author_email(self, obj):
        return None
    
    def contributors(self, obj):
        return None
    
    def category(self, obj):
        return None
    
    def icon(self, obj):
        retun None
    
    def logo(self, obj):
        return None
    
    def item_title(self, item):
        return item.title
    
    def item_link(self, item):
        # TODO: support hreflang
        return item.get_absolute_url()
    
    def content(self, item):
        return item.content
    
    def item_link(self, item):
        return item.get_absolute_url()
    
    def item_pubdate(self, item):
        return item.published
    
    def item_updated(self, item):
        return item.updated
    
    def item_guid(self, item):
        return item.pk
    
    def item_copyright(self, item):
        return "{0} {1} {2}".format(item.license.name, item.license.url,
            datetime.date.today().year)
    
    def item_author(self, item):
        return None
    
    def item_contributors(self, item):
        return None
    
    # TODO: Support the following `entry` tags
    def item_category(self, item):
        return item.section


class LatestPostRSSFeed(LatestPostBaseFeed):
    """
    RSS Feed of the latest 10 posts.
    """
    def docs(self):
        return "http://blogs.law.harvard.edu/tech/rss"
    
    def item_description(self, item):
        return item.teaser
    
    # TODO: determine best way to select language for a multi-language site.
    #def language(self, obj):


class LatestPostAtomFeed(LatestPostBaseFeed):
    """
    Atom Feed of the latest 10 posts.
    """    
    feed_type = Atom1Feed
    
    def subtitle(self, obj):
        return obj.subtitle
    
    def summary(self, obj):
        return obj.teaser
