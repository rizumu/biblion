from django.contrib import admin
from django.conf import settings
from django.utils.functional import curry

from biblion.models import Blog, Post, Image
from biblion.forms import AdminBlogForm, AdminPostForm
from biblion.utils.twitter import can_tweet


class BlogAdmin(admin.ModelAdmin):
    list_display = ["title", "published_flag", "site"]
    prepopulated_fields = {"slug": ("title",)}
    form = AdminBlogForm
    
    def published_flag(self, obj):
        return bool(obj.published)
    published_flag.short_description = "Published"
    published_flag.boolean = True
    
    def save_form(self, request, form, change):
        # this is done for explicitness that we want form.save to commit
        # form.save doesn't take a commit kwarg for this reason
        return form.save()


class ImageInline(admin.TabularInline):
    model = Image
    fields = ["image_path"]


class PostAdmin(admin.ModelAdmin):  
    list_display = ["blog", "title", "published_flag", "section"]
    list_filter = ["section"]
    form = AdminPostForm
    fields = [
        "blog",
        "section",
        "title",
        "slug",
        "authors",
        "contributors",
        "license",
        "teaser",
        "content",
        "markup_type",
        "publish",
        "comments",
    ]
    if can_tweet():
        fields.append("tweet_text")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [
        ImageInline,
    ]
    
    def __init__(self, *args, **kwargs):
        if "taggit" in settings.INSTALLED_APPS:
            self.fields.append("tags")
        super(PostAdmin, self).__init__(*args, **kwargs)
    
    def published_flag(self, obj):
        return bool(obj.published)
    published_flag.short_description = "Published"
    published_flag.boolean = True
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs["request"]
        if db_field.name == "authors":
            ff = super(PostAdmin, self).formfield_for_dbfield(db_field, **kwargs)
            ff.initial = [request.user.id]
            return ff
        return super(PostAdmin, self).formfield_for_dbfield(db_field, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        kwargs.update({
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        })
        return super(PostAdmin, self).get_form(request, obj, **kwargs)
    
    def save_form(self, request, form, change):
        # this is done for explicitness that we want form.save to commit
        # form.save doesn't take a commit kwarg for this reason
        return form.save()


admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Image)
