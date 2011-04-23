from django.conf.urls.defaults import patterns, url

from biblion.feeds import LatestPostRSSFeed, LatestPostAtomFeed


urlpatterns = patterns("",
    url(r"^(?P<blog_slug>[-\w]+)/rss/$", LatestPostRSSFeed(), name="blog_feed_rss"),
    url(r"^(?P<blog_slug>[-\w]+)/atom/$", LatestPostAtomFeed(), name="blog_feed_atom"),
)
