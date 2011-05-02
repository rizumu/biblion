from datetime import datetime

from django import forms
from django.utils.translation import ugettext as _

from biblion.models import Blog, Post, Revision
from biblion.utils.twitter import can_tweet


class AdminBlogForm(forms.ModelForm):
    
    publish = forms.BooleanField(
        required = False,
        help_text = _("Checking this will publish this blog on the site"),
    )
    
    class Meta:
        model = Blog
    
    def save(self):
        blog = super(AdminBlogForm, self).save(commit=False)
        
        if blog.pk is None:
            if self.cleaned_data["publish"]:
                blog.published = datetime.now()
        else:
            if Blog.objects.filter(pk=blog.pk, published=None).count():
                if self.cleaned_data["publish"]:
                    blog.published = datetime.now()

        blog.updated = datetime.now()
        blog.save()

        return blog


class AdminPostForm(forms.ModelForm):
    
    title = forms.CharField(
        max_length = 90,
        widget = forms.TextInput(
            attrs = {"style": "width: 50%;"},
        ),
    )
    slug = forms.CharField(
        widget = forms.TextInput(
            attrs = {"style": "width: 50%;"},
        )
    )
    teaser = forms.CharField(
        widget = forms.Textarea(
            attrs = {"style": "width: 80%;"},
        ),
    )
    content = forms.CharField(
        widget = forms.Textarea(
            attrs = {"style": "width: 80%; height: 300px;"},
        )
    )
    publish = forms.BooleanField(
        required = False,
        help_text = _("Checking this will publish this article on the site"),
    )
    
    if can_tweet():
        tweet = forms.BooleanField(
            required = False,
            help_text = _("Checking this will send out a tweet for this post"),
        )
    
    class Meta:
        model = Post
    
    def __init__(self, *args, **kwargs):
        super(AdminPostForm, self).__init__(*args, **kwargs)
        
        post = self.instance
        
        # grab the latest revision of the Post instance
        latest_revision = post.latest()
        
        if latest_revision:
            # set initial data from the latest revision
            self.fields["teaser"].initial = latest_revision.teaser
            self.fields["content"].initial = latest_revision.content
        
            # @@@ can a post be unpublished then re-published? should be pulled
            # from latest revision maybe?
            self.fields["publish"].initial = bool(post.published)
    
    def save(self):
        post = super(AdminPostForm, self).save(commit=False)
        
        if post.pk is None:
            if self.cleaned_data["publish"]:
                post.published = datetime.now()
        else:
            if Post.objects.filter(pk=post.pk, published=None).count():
                if self.cleaned_data["publish"]:
                    post.published = datetime.now()
        
        post.teaser = self.cleaned_data["teaser"]
        post.content = self.cleaned_data["content"]
        post.updated = datetime.now()
        post.save()
        
        r = Revision()
        r.post = post
        r.title = post.title
        r.teaser = self.cleaned_data["teaser"]
        r.content = self.cleaned_data["content"]

        r.updated = post.updated
        r.published = post.published
        r.save() # must save to set pk before adding a m2m field
        r.authors = post.authors.all()
        r.save()
        
        if can_tweet() and self.cleaned_data["tweet"]:
            post.tweet()
        
        return post
