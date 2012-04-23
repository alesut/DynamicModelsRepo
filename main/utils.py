#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.db import connection
from django.db import models
from django.contrib.admin.sites import NotRegistered
from django.core.urlresolvers import clear_url_caches
from django.utils.importlib import import_module
from django.db.models.loading import cache
from django.conf import settings

import logging
from south.db import db


def unregister_from_admin(admin_site, model):
    """ Removes the dynamic model from the given admin site """

    # First deregister the current definition
    # This is done "manually" because model will be different
    # db_table is used to check for class equivalence.
    for reg_model in admin_site._registry.keys():
        if model._meta.db_table == reg_model._meta.db_table:
            del admin_site._registry[reg_model]

    # Try the normal approach too
    try:
        admin_site.unregister(model)
    except NotRegistered:
        pass

    # Reload the URL conf and clear the URL cache
    # It's important to use the same string as ROOT_URLCONF
    reload(import_module(settings.ROOT_URLCONF))
    clear_url_caches()


def reregister_in_admin(admin_site, model, admin_class=None):
    """ (re)registers a dynamic model in the given admin site """

    # We use our own unregister, to ensure that the correct
    # existing model is found 
    # (Django's unregister doesn't expect the model class to change)
    unregister_from_admin(admin_site, model)
    admin_site.register(model, admin_class)

    # Reload the URL conf and clear the URL cache
    # It's important to use the same string as ROOT_URLCONF
    reload(import_module(settings.ROOT_URLCONF))
    clear_url_caches()


def create_db_table(model_class):
    """ Takes a Django model class and create a database table, if necessary.
    """
    table_name = model_class._meta.db_table
    if (connection.introspection.table_name_converter(table_name)
        not in connection.introspection.table_names()):
        fields = [(f.name, f) for f in model_class._meta.fields]
        db.create_table(table_name, fields)
        logging.debug("Creating table '%s'" % table_name)
        return True
    else:
        return False


def add_necessary_db_columns(model_class):
    """ Creates new table or relevant columns as necessary based on the model_class.
      No columns or data are renamed or removed.
    """
    # Create table if missing
    create_db_table(model_class)

    # Add field columns if missing
    table_name = model_class._meta.db_table
    fields = [(f.column, f) for f in model_class._meta.fields]
    table_description = connection.introspection.get_table_description(
        connection.cursor(), table_name)
    db_column_names = [row[0] for row in table_description]
    for column_name, field in fields:
        if column_name not in db_column_names:
            logging.debug("Adding field '%s' to table '%s'" % (
                column_name, table_name))
            db.add_column(table_name, column_name, field)


def generate_model_class(model_name, model_dict):
    """ Generate new model class based on model name and model dict with
        models attributes.
    """
    _app_label = 'main'
    _db_table = "main_%s" % model_name
    _model_name = model_name
    # Remove any exist model definition from Django's cache
    try:
        del cache.app_models[_app_label][_model_name.lower()]
    except KeyError:
        pass
    # Build the class attributes here
    attrs = {}
    # Create the relevant meta information
    class Meta:
        app_label = _app_label
        db_table = _db_table
        managed = False
        verbose_name = model_dict.get('title')
        verbose_name_plural = model_dict.get('title')
    attrs['__module__'] = 'main.models'
    attrs['Meta'] = Meta
    # Create fields for model
    for field in model_dict.get('fields'):
        field_id = field.get('id')
        field_name = field.get('title')
        field_type = field.get('type')
        if field_id and field_name and field_type:
            if field_type == 'char':
                attrs[field_id] = models.CharField(max_length=255,
                    verbose_name=field_name, blank=True)
            elif field_type == "int":
                attrs[field_id] = models.IntegerField(verbose_name=field_name,
                    default=0, blank=True, null=True)
            else:
                continue
    # Add representative function
    attrs["__unicode__"] = lambda self: str(self.id)
    # Create the new model class
    model_class = type(_model_name, (models.Model,), attrs)
    return model_class

