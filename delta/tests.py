"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from delta.models import *

class DiffTest(TestCase):
	def diff_and_compare(self):
		pass

class VersionControlTest(TestCase):
	def populate(self):
		pass
		
	def get_version_test(self):
		pass
		
	def revert_test(self):
		pass
		
	