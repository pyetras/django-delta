from django.conf.urls.defaults import *
from delta.models import *
import os
info = {
	'queryset' : DeltaText.objects.all(),
}

urlpatterns = patterns('',
	(r'^$', 'django.views.generic.list_detail.object_list', info, 'deltatext-list'), 
	url(r'^(?P<file_id>\d+)/$', 'delta_example.views.detail',
	 	 name='deltatext-detail'),
	url(r'^(?P<file_id>\d+)/(?P<version_number>\d+)/$', 'delta_example.views.detail',
	 	 name='deltatext-detail'),
	url(r'^(?P<file_id>\d+)/revert-to/(?P<version_number>\d+)/$', 'delta_example.views.revert',
	 	 name='deltatext-revert'),
	url(r'^(?P<file_id>\d+)/restore-to/(?P<version_number>\d+)/$', 'delta_example.views.restore',
	 	 name='deltatext-restore'),
	(r'^add/$', 'django.views.generic.create_update.create_object', 
		{'model':DeltaText, 'post_save_redirect':'/delta/%(id)s/'}, 'deltatext-add'),
	(r'^update/(?P<object_id>\d+)/$', 'django.views.generic.create_update.update_object', 
		{'model':DeltaText, 'post_save_redirect':'/delta/%(id)s/'}, 'deltatext-update'),
	(r'^delete/(?P<object_id>\d+)/$', 'django.views.generic.create_update.delete_object', 
		{'model':DeltaText, 'post_delete_redirect':'/delta/'}, 'deltatext-delete'),
	(r'^media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': os.path.dirname(os.path.abspath(__file__))+'/media'}),
	
)