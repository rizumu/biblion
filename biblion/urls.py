from django.conf.urls.defaults import patterns, url


urlpatterns = patterns("",
    url(r"^$",
        "biblion.views.blog_list", name="blog_list"),
    url(r"^(?P<blog_slug>[-\w]+)/$",
        "biblion.views.blog_detail", name="blog_detail"),
    url(r"^(?P<blog_slug>[-\w]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$",
        "biblion.views.blog_post_detail", name="blog_post"),
    url(r"^(?P<blog_slug>[-\w]+)/post/(?P<post_pk>\d+)/$",
        "biblion.views.blog_post_detail", name="blog_post_pk"),
    url(r"^(?P<blog_slug>[-\w]+)/(?P<section>[-\w]+)/$",
        "biblion.views.blog_section_list", name="blog_section"),
)
