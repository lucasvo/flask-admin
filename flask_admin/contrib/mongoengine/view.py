from flask.ext import wtf
from flask.ext.admin.model import BaseModelView
from flask.ext.admin.contrib.mongoengine import filters
from flask.ext.mongoengine.wtf import model_form
from flask.ext.mongoengine.wtf.models import ModelForm
from flask.ext.mongoengine.wtf.orm import ModelConverter, converts

from mongoengine import ReferenceField


class AdminModelForm(ModelForm):
    def save(self, commit=True):
        if self.instance:
            update = {}
            for name, field in self._fields.iteritems():
                try:
                    if getattr(self.instance, name) != field.data:
                        update['set__' + name] = field.data
                except AttributeError:
                    pass
            update['commit'] = commit
            self.instance.update(**update)
        else:
            self.instance = self.model_class(**self.data)
            if commit:
                self.instance.save(validate=False)
        return self.instance


class AdminModelConverter(ModelConverter):
    @converts('EmbeddedDocumentField')
    def conv_EmbeddedDocument(self, model, field, kwargs):
        kwargs = {
            'validators': [],
            'filters': [],
        }
        form_class = model_form(field.document_type_obj, base_class=AdminModelForm, converter=self.__class__(), field_args={})
        def get_form_class(*args, **kwargs):
            kwargs['csrf_enabled'] = False
            return form_class(*args, **kwargs)
        return wtf.FormField(get_form_class, **kwargs)


class ModelView(BaseModelView):
    model_converter_class = AdminModelConverter
    base_form_class = AdminModelForm

    def scaffold_filters(self, name):
        # TODO: more filters
        options = None

        if isinstance(self.model._fields[name], ReferenceField):
            options = [(obj.id, unicode(obj)) for obj in self.model._fields[name].document_type.objects.all()]
            return [filters.EqualsFilter(name, options)]
        else:
            return [filters.ContainsFilter(name, options)]

    def get_pk_value(self, instance):
        return instance.id

    def scaffold_list_columns(self):
        columns = []
        exclude = self.excluded_list_columns or []

        for p in self.model._fields.keys():
            if p not in exclude:
                columns.append(p)

        return columns

    def scaffold_sortable_columns(self):
        return {}

    def scaffold_form(self):
        return model_form(self.model, base_class=self.base_form_class, converter=self.model_converter_class())

    def create_form(self, form, obj=None):
        return self._edit_form_class(form, obj=obj)

    def edit_form(self, form, obj=None):
        return self._edit_form_class(form, obj=obj)

    def get_one(self, id):
        return self.model.objects.get(pk=id)

    def get_list(self, page, sort_field, sort_desc, search, filters):
        qs = self.model.objects

        if filters:
            for flt, value in filters:
                qs = self._filters[flt].apply(qs, value)

        count = qs.count()
        skip = int(page or 0)*self.page_size

        if sort_field:
            if sort_desc:
                qs = qs.order_by('-' + sort_field)
            else:
                qs = qs.order_by(sort_field)

        qs = qs[skip:skip+self.page_size]
        return count, qs

    def update_model(self, form, instance):
        form.save()
        return True

    def create_model(self, form):
        form.save()
        return True

    def delete_model(self, instance):
        instance.delete()
        return True
