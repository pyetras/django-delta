from django.shortcuts import render_to_response, get_object_or_404
from delta.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse

class VersionsForm(forms.Form):
	versions = forms.ChoiceField()

def detail(request, file_id, version_number = 0):
	if request.method == "POST":
		pass
	else:
		version_number = (version_number != '' or version_number == None) and int(version_number) or 0
		file = get_object_or_404(DeltaText, id = file_id)
		
		form = VersionsForm()
		tab = [(i, i) for i in range(1, file.version_count()+1)]
		form.fields['versions'].choices = tab
		
		try:
			file.ver(version_number)
		except Version.DoesNotExist:
			file.ver(0)

		file.version.number += 1
		form.fields['versions'].initial = file.version.number
		return render_to_response('delta/deltatext_detail.html', {
			'file': file,
			'form': form,
		})
	
def revert(request, file_id, version_number):
	file = get_object_or_404(DeltaText, id = file_id)
	file.revert(int(version_number))
	return HttpResponseRedirect(reverse(detail, args=(file_id,)))
	
def restore(request, file_id, version_number):
	file = get_object_or_404(DeltaText, id = file_id)
	file.restore(int(version_number))
	return HttpResponseRedirect(reverse(detail, args=(file_id,)))

	