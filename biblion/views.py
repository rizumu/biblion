from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404

from django.contrib.sites.models import Site

from biblion.exceptions import InvalidSection
from biblion.models import Blog, Post
from biblion.settings import ALL_SECTION_NAME


def blog_list(request, site_id=None, **kwargs):
    """
    All active blogs for a given site, current_site if unspecified.
    """
    if site_id == None:
        blogs = Blog.objects.active().onsite()
    else:
        blogs = Blog.objects.active().filter(id=site_id)
    context = {
        "blogs": blogs,
        "posts": Post.objects.current().filter(blog__in=blogs),
    }
    context.update(kwargs)
    return render_to_response("biblion/blog_list.html", context,
        context_instance=RequestContext(request))


def blog_detail(request, blog_slug):
    """ All published posts for a given blog. """
   
    blog = Blog.objects.get(slug=blog_slug)
    posts = Post.objects.current().filter(blog=blog).exclude(published=None)
    
    return render_to_response("biblion/blog_detail.html", {
        "posts": posts,
    }, context_instance=RequestContext(request))


def blog_section_list(request, blog_slug, section):
    
    try:
        posts = Post.objects.onsite().section(section)
    except InvalidSection:
        raise Http404()
    
    return render_to_response("biblion/blog_section_list.html", {
        "section_slug": section,
        "section_name": dict(Post.SECTION_CHOICES)[Post.section_idx(section)],
        "posts": posts,
    }, context_instance=RequestContext(request))


def blog_post_detail(request, blog_slug, **kwargs):
    
    if "post_pk" in kwargs:
        if request.user.is_authenticated() and request.user.is_staff:
            queryset = Post.objects.all()
            post = get_object_or_404(queryset, pk=kwargs["post_pk"])
        else:
            raise Http404()
    else:
        queryset = Post.objects.current()
        queryset = queryset.filter(
            published__year = int(kwargs["year"]),
            published__month = int(kwargs["month"]),
            published__day = int(kwargs["day"]),
        )
        post = get_object_or_404(queryset, slug=kwargs["slug"])
        post.inc_views()
    
    return render_to_response("biblion/blog_post_detail.html", {
        "post": post,
    }, context_instance=RequestContext(request))
