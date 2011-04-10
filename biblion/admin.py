from django.contrib import admin
from django.utils.functional import curry

from biblion.models import Blog, Post, Image
from biblion.forms import AdminPostForm
from biblion.utils.twitter import can_tweet


class BlogAdmin(admin.ModelAdmin):
    list_display = ["title", "active_flag", "site"]
    prepopulated_fields = {"slug": ("title",)}

    def active_flag(self, obj):
        return bool(obj.active)
    active_flag.short_description = "Active"
    active_flag.boolean = True


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
        "teaser",
        "content",
        "markup_type",
        "publish",
        "comments",
    ]
    if can_tweet():
        fields.append("tweet")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [
        ImageInline,
    ]
    
    def published_flag(self, obj):
        return bool(obj.published)
    published_flag.short_description = "Published"
    published_flag.boolean = True
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request")
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
