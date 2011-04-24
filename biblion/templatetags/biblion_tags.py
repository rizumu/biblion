from django import template
from django.shortcuts import get_object_or_404

from biblion.models import Blog, Post
from biblion.settings import ALL_SECTION_NAME, SECTIONS
from biblion.utils.code_hilite import to_html


register = template.Library()


register.filter("to_html", to_html)


class LatestBlogPostsNode(template.Node):
    
    def __init__(self, blog_slug, quantity, context_var):
        self.blog = get_object_or_404(Blog, slug=blog_slug)
        self.quantity = quantity
        self.context_var = context_var
    
    def render(self, context):
        latest_posts = Post.objects.filter(blog=self.blog).current()[:self.quantity]
        context[self.context_var] = latest_posts
        return u""


@register.tag
def latest_blog_posts(parser, token):
    """
        {% latest_blog_posts blog.slug 1 as latest_blog_posts %}
    """
    bits = token.split_contents()
    return LatestBlogPostsNode(bits[1], int(bits[2]), bits[4])


class LatestSectionPostNode(template.Node):
    
    def __init__(self, section, context_var):
        self.section = template.Variable(section)
        self.context_var = context_var
    
    def render(self, context):
        section = self.section.resolve(context)
        post = Post.objects.section(section, queryset=Post.objects.current())
        try:
            post = post[0]
        except IndexError:
            post = None
        context[self.context_var] = post
        return u""


@register.tag
def latest_section_post(parser, token):
    """
        {% latest_section_post "articles" as latest_article_post %}
    """
    bits = token.split_contents()
    return LatestSectionPostNode(bits[1], bits[3])


class BlogSectionsNode(template.Node):
    
    def __init__(self, context_var):
        self.context_var = context_var
    
    def render(self, context):
        sections = [(ALL_SECTION_NAME, "All")] + SECTIONS
        context[self.context_var] = sections
        return u""


@register.tag
def blog_sections(parser, token):
    """
        {% blog_sections as blog_sections %}
    """
    bits = token.split_contents()
    return BlogSectionsNode(bits[2])


def show_post_brief(context, post):
    return {
        "post": post,
        "last": context["forloop"]["last"],
        "can_edit": context["user"] in post.blog.maintainers.all(),
    }
register.inclusion_tag("biblion/_post_brief.html", takes_context=True)(show_post_brief)
