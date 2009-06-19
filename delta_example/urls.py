from django.conf.urls.defaults import *
from delta.models import *
import os
info = {
	'queryset' : VCFile.objects.all(),
}

urlpatterns = patterns('',
	(r'^$', 'django.views.generic.list_detail.object_list', info, 'vcfile-list'), 
	url(r'^(?P<file_id>\d+)/$', 'delta_example.views.detail',
	 	 name='vcfile-detail'),
	url(r'^(?P<file_id>\d+)/(?P<version_number>\d+)/$', 'delta_example.views.detail',
	 	 name='vcfile-detail'),
	url(r'^(?P<file_id>\d+)/revert-to/(?P<version_number>\d+)/$', 'delta_example.views.revert',
	 	 name='vcfile-revert'),
	(r'^add/$', 'django.views.generic.create_update.create_object', 
		{'model':VCFile, 'post_save_redirect':'/delta/%(id)s/'}, 'vcfile-add'),
	(r'^update/(?P<object_id>\d+)/$', 'django.views.generic.create_update.update_object', 
		{'model':VCFile, 'post_save_redirect':'/delta/%(id)s/'}, 'vcfile-update'),
	(r'^delete/(?P<object_id>\d+)/$', 'django.views.generic.create_update.delete_object', 
		{'model':VCFile, 'post_delete_redirect':'/delta/'}, 'vcfile-delete'),
	(r'^media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': os.path.dirname(os.path.abspath(__file__))+'/media'}),
	
)