from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib import admin
from django.utils import simplejson as json
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import yaml
import os.path
from utils import (generate_model_class, add_necessary_db_columns,
                   reregister_in_admin)

APP_PATH = os.path.dirname(__file__)
APP_NAME = 'main'
MODELS_FILE = os.path.join(APP_PATH, 'models.yml')

def index(request):
    my_data_dictionary = {'tables_titles':[]}
    for model in admin.site._registry.keys():
        if model._meta.app_label == APP_NAME:
            my_data_dictionary['tables_titles'].append({
                'title': model._meta.verbose_name_plural,
                'db_title': model._meta.db_table
            })
    return render_to_response('main.html', my_data_dictionary,
        context_instance=RequestContext(request))


def create_models(request):
    if request.method == 'POST' and request.FILES:
        file_with_models = request.FILES.get('models')
        try:
            models = yaml.load(file_with_models.read())
        except yaml.YAMLError:
            return HttpResponseRedirect(reverse('index'))
        for model in models:
            model_class = generate_model_class(model, models[model])
            add_necessary_db_columns(model_class)
            reregister_in_admin(admin.site, model_class)
    return HttpResponseRedirect(reverse('index'))


def receive_table_content(request):
    if request.method == "GET" and request.GET:
        table_name = request.GET.get('table_name')
        if not table_name:
            return HttpResponse(json.dumps(0), mimetype='application/json')
        for model in admin.site._registry.keys():
            if model._meta.db_table == table_name:
                fields_names = [field.verbose_name
                                for field in model._meta.fields]
                fields = [field.name for field in model._meta.fields]
                body = []
                items = model.objects.all()
                for item in items:
                    instance = []
                    for field in fields:
                        instance.append(item.__dict__.get(field))
                    body.append(instance)
                table_contend_dict = {
                    'head': fields_names,
                    'body': body
                }
                return HttpResponse(
                    json.dumps(table_contend_dict),
                    mimetype='application/json')
    return HttpResponse(json.dumps(0), mimetype='application/json')