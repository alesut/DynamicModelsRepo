from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'main.views.index', name='index'),
    url(r'^create_models_from_file/$', 'main.views.create_models'),
    url(r'^receive_table_content/$', 'main.views.receive_table_content'),
    url(r'^admin/', include(admin.site.urls)),
)
