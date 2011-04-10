from django.db.models.query import Q

from django.contrib.sites.models import Site

from biblion.exceptions import InvalidSection
from biblion.settings import ALL_SECTION_NAME


class BlogManager(object):

    def active(self):
        return self.exclude(active=None)

    def onsite(self):
        return self.filter(site=Site.objects.get_current())


class PostManager(object):
    
    def published(self):
        return self.exclude(published=None)
    
    def current(self):
        return self.published().order_by("-published")
    
    def onsite(self):
        return self.filter(blog__site=Site.objects.get_current())
    
    def section(self, value, queryset=None):
        
        if queryset is None:
            queryset = self.published()
        
        if not value:
            return queryset
        else:
            try:
                section_idx = self.model.section_idx(value)
            except KeyError:
                raise InvalidSection
            all_sections = Q(section=self.model.section_idx(ALL_SECTION_NAME))
            return queryset.filter(all_sections | Q(section=section_idx))
