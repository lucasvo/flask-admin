from flask.ext.admin.babel import gettext
from flask.ext.admin.model import filters

class ContainsFilter(filters.BaseFilter):
    def operation(self):
        return gettext('contains')

    def apply(self, query, value):
        return query.filter(**{self.name+'__icontains': value})

class EqualsFilter(filters.BaseFilter):
    def operation(self):
        return gettext('equals')

    def apply(self, query, value):
        return query.filter(**{self.name: value})

