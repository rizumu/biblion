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


class LatestPostRSSFeed(Feed):
    """
    Feed of the latest 10 posts.
    """
    def get_object(self, request, blog_slug, site=Site.objects.get_current()):
        if request:
            # create a feed hit
            hit = FeedHit()
            hit.request_data = serialize_request(request)
            hit.save()
        return get_object_or_404(Blog, slug=blog_slug, site=site)

    def title(self, obj):
        return "%s feed" % obj

    def description(self, obj):
        return obj.description

    def link(self, obj):
        return reverse("blog_detail", args=[obj.slug])
    
    def items(self, obj):
        return Post.objects.published().filter(blog=obj)[:10]

    #def item_pubdate(self, obj):
    #    latest_post = Post.objects.filter(blog=obj).latest()
    #    return latest_post.published


class LatestPostAtomFeed(LatestPostRSSFeed):
    """
    Feed of the latest 10 posts.
    """    
    feed_type = Atom1Feed
    subtitle = LatestPostRSSFeed.description
    def summary(self, obj):
        return obj.description
