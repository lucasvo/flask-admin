from flask.ext.admin.model import BaseModelView
from flask.ext.mongoengine.wtf import model_form
from flask.ext.mongoengine.wtf.models import ModelForm
from flask.ext.mongoengine.wtf.orm import ModelConverter, converts

from flask.ext import wtf


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
        form_class = model_form(field.document_type_obj, base_class=AdminModelForm, converter=AdminModelConverter(), field_args={})
        def get_form_class(*args, **kwargs):
            kwargs['csrf_enabled'] = False
            return form_class(*args, **kwargs)
        return wtf.FormField(get_form_class, **kwargs)


class ModelView(BaseModelView):
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
        return model_form(self.model, base_class=AdminModelForm, converter=AdminModelConverter())


    def create_form(self, form, obj=None):
        return self._edit_form_class(form, obj=obj)

    def edit_form(self, form, obj=None):
        return self._edit_form_class(form, obj=obj)

    def get_one(self, id):
        return self.model.objects.get(pk=id)

    def get_list(self, page, sort_field, sort_desc, search, filters):
        # TODO: finish implementation
        qs = self.model.objects
        return qs.count(), qs.all()

    def update_model(self, form, instance):
        form.save()
        return True

    def create_model(self, form):
        form.save()
        return True
