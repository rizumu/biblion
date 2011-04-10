from django.db import models
from django.db.models.query import Q

from biblion.exceptions import InvalidSection
from biblion.settings import ALL_SECTION_NAME


class BlogManager(models.Manager):

    def active(self):
        return self.exclude(active=None)


class PostManager(models.Manager):
    
    def published(self):
        return self.exclude(published=None)
    
    def current(self):
        return self.published().order_by("-published")
    
    def section(self, value, queryset=None):
        
        if queryset is None:
            queryset = self.published().filter(blog=self.blog)
        
        if not value:
            return queryset
        else:
            try:
                section_idx = self.model.section_idx(value)
            except KeyError:
                raise InvalidSection
            all_sections = Q(section=self.model.section_idx(ALL_SECTION_NAME))
            return queryset.filter(all_sections | Q(section=section_idx))
