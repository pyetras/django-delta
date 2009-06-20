from delta.models import *
from django.contrib import admin

class VCFileAdmin(admin.ModelAdmin):
	list_display = ('head_short', 'version_count', 'last_edit', 'date_created')
	def head_short(self, obj):
		return obj.head[:100] + (len(obj.head)>100)*'...'
	head_short.short_description = 'Head'
		
admin.site.register(VCFile, VCFileAdmin)

class VersionAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'delta_short', 
	'date_commited')
	date_hierarchy = 'date_commited'
	
	def delta_short(self, obj):
		return obj.delta[:100] + (len(obj.delta)>100)*'...'
	delta_short.short_description = 'Delta'
	
admin.site.register(Version, VersionAdmin)