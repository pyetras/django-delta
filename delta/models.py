from django.db import models
from django.conf import settings
import base64
from django.db import connection

class DeltaText(models.Model):
	id = models.AutoField(primary_key = True)
	head = models.TextField()
	version = None
				
	def save(self, commit = True, forceNewTree = False):
		"""
			Any changes made to head field are automatically commited into new Version,
			unless commit = False.
		"""
		self.head = self.head.replace('\r', '')
		if self.head[-1] != '\n': self.head += '\n'
		super(DeltaText, self).save()
		
		if commit:
			self.commitChanges(forceNewTree)
			
	def delete(self):
		self.version_set.delete()
		return super(DeltaText, self).delete()
			
	@staticmethod			
	def computeDelta(str1, str2):
		"""
			Computes delta of two strings (split by \\n) using SequenceMatcher.difflib
		"""
		from difflib import SequenceMatcher
		
		a = str1.split('\n')		
		a = map(lambda x: x+'\n', a[:-1])

		b = str2.split('\n')
		b = map(lambda x: x+'\n', b[:-1])

		s = SequenceMatcher(None, a, b)
		diff = []
		for opcode in s.get_opcodes():
			if opcode[0] == 'replace' or opcode[0] == 'delete':
				diff.append('-%d %d'%(opcode[1], opcode[2]))
			if opcode[0] == 'replace' or opcode[0] == 'insert':
				diff.append('+%d %s'%(opcode[2], 
				''.join(b[opcode[3]:opcode[4]])))
		return diff
	
		
	def commitChanges(self, forceNewTree = False):
		"""
			Commits changes made on self.head to a new Version.
		"""
		
		max_degree = getattr(settings, 'MAX_DEGREE', 10)
		max_depth = getattr(settings, 'MAX_DEPTH', 100)

		count = self.version_count()
		v = Version(file = self)

		if (count) % (max_depth*max_degree) == 0 or forceNewTree: #new tree
			str1 = ''
			differs = None
		else:
			if (count - 1) % max_degree == 0: #new key node
				which = count - 1
			else: #new node
				which = ((count-1)/max_degree)*max_degree
			differs = self.version_set.order_by('date_commited')[which]
			str1 = differs.recover().file_unpacked
		
		if count > 0:
			prev = self.getVersion(count)
			if prev.file_unpacked == self.head: return
		
		delta = DeltaText.computeDelta(str1, self.head)
		#if delta == [] and count > 0: return
		
		v.setDelta(delta)
		v.differs = differs
		v.save()
		
		self.count = -1

	def revert(self, number):
		"""
			Deletes all versions newer than number.
		"""
		v = self.getVersion(number)
		self.version_set.filter(date_commited__gt = v.date_commited).delete()
		
		self.head = v.file_unpacked
		self.save(commit = False)
		
		self.count = -1

	def restore(self, number):
		"""
			Restores DeltaText to a specified Version by appending DeltaText.version_set
			with that version.
		"""
		v = self.getVersion(number)
		v_new = Version(delta = v.delta, differs = v.differs, file = v.file)
		v_new.save()
		v_new.file_unpacked = v.file_unpacked
		
		self.version = v_new
		
		self.head = v.file_unpacked
		self.save(commit = False)
		
		self.count = -1
		

	def getVersion(self, number=1):
		"""
			Get and unpack a specific version object for DeltaText.
			number can be 0 - returns the most recent version; positive - returns
			the corresponding version (by 1-based index); or negative (-1 returns the previous
			version and so on)
			Returns Version object.
		"""
		count = self.version_count()
		
		if number == 0:
			v = self.version_set.order_by('date_commited')[count-1]
			v.file_unpacked = self.head
			v.number = count - 1
			return v

		if number < 0:
			number += count

		number -= 1
		v = self.version_set.select_related('differs').order_by('date_commited')[number].recover()
		v.number = number 
		return v
	
	def listVersions(self):
		"""
			Lists the whole version_set tree, for debugging and awesomeness puproses.
		"""
		versions = ['']
		for i, v in enumerate(Version.objects.get_with_number(self)):
			versions.append(v.applyDelta(versions[v.differs and v.differs.number+1 or 0]))
			yield v
	
	def ver(self, number):
		"""
			Shortcut for DeltaText.getVersion.
			Returns DeltaText (self).
		"""
		self.version = self.getVersion(number)
		return self
		
	def rtext(self):
		"""
			Returns currently selected version's head (Version.file_unpacked).
			(A version is selected after calling DeltaText.ver)
		"""
		try:
			return self.version.file_unpacked
		except AttributeError:
			return self.head
			
	def rtext_list(self):
		return self.rtext().split('\n')[:-1]
	
	def last_edit(self):
		"""
			Returns latest (for DeltaText.version_set) Version's 'date_commited'
		"""
		if self.pk:
			return self.version_set.only('date_commited').order_by('-date_commited')[0].date_commited
		
	__date_created = None
	def date_created(self):
		"""
			Returns first (for DeltaText.version_set) Version's 'date_commited'.
			Cached in DeltaText.date_created
		"""
		if self.pk:
			if self.__date_created == None:
				self.__date_created = self.version_set.only('date_commited').order_by('date_commited')[0].date_commited
			return self.__date_created
		
	count = -1
	def version_count(self, force = False):
		"""
			Returns count of Versions in version_set.
			Cached in DeltaText.count.
		"""
		if self.count < 0 or force:
			self.count = self.version_set.count()
		return self.count
	version_count.short_description = 'Versions'
		
	def head_list(self):
		return self.head.split('\n')[:-1];
		
	def __unicode__(self):
		return self.head
		
	class Meta:
		ordering = ('-id',)
	
class VersionManager(models.Manager):
	use_for_related_fields = True
	def get_with_number(self, file):
		cursor = connection.cursor()
		cursor.execute("""
			SELECT v.id, v.delta, v.date_commited, COUNT(other.id) AS number, v.differs_id
			FROM delta_version v LEFT OUTER JOIN delta_version other ON 
			other.file_id = %s AND other.date_commited < v.date_commited
			WHERE v.file_id = %s
			GROUP BY v.id, v.delta, v.date_commited
			ORDER BY v.date_commited ASC;
		""", [file.pk, file.pk])
		versions = {}
		for row in cursor.fetchall():
			v = self.model(id = row[0], delta = row[1], date_commited = row[2], file = file)
			v.number = row[3]
			versions[v.id] = v
			if row[4]:
				v.differs = versions[int(row[4])]
			yield v
		
class Version(models.Model):
	use_zlib = getattr(settings, 'USE_ZLIB', False)
	
	id = models.AutoField(primary_key = True)
	number = None
	delta = models.TextField(editable = False)
	#can be upgraded with http://www.djangosnippets.org/snippets/1495/
	differs = models.ForeignKey('Version', null = True)
	file = models.ForeignKey('DeltaText')
	date_commited = models.DateTimeField(auto_now_add = True)
	file_unpacked = ''
	
	objects = VersionManager()
	
	def setDelta(self, delta_list):	
		if delta_list == None:
			self.delta = ''
			
		self.delta = '\1'.join(delta_list)
		if self.use_zlib:
			self.delta = base64.encodestring(self.delta.encode('utf-8').encode('zlib'))
	
	def save(self):
		if self.delta is list:
			self.setDelta(self.delta)
		super(Version, self).save()
	
	def getDelta(self):
		if self.delta is list: return self.delta
		if self.delta == '': return []
		
		if self.use_zlib:
			return base64.decodestring(self.delta).decode('zlib').decode('utf-8').split('\1')
		
		return self.delta.split('\1')
	
	def applyDelta(self, str1):
		delta_list = self.getDelta()
		
		if len(delta_list)==0: 
			self.file_unpacked = str1
			return str1

		a = str1.split('\n')[:-1]
		a = map(lambda x: x+'\n', a)	

		res = ''
		ida = 0
		delta_list.append('-%d %d'%(len(a), len(a)))

		for d in delta_list:
			ch = d[0]
			d = d[1:].split(' ', 1)

			s = int(d[0])
			res += s - ida > 0 and ''.join(a[ida:s]) or ''	
			ida = s		

			if ch == '-':			
				ida = int(d[1].split(' ',1)[0])
			elif ch == '+':
				res += d[1]
		self.file_unpacked = res
		return res
	
	def recover(self):
		if self.differs != None:
			orig = self.differs.recover().file_unpacked
		else:
			orig = ''

		self.applyDelta(orig)
		return self
			
	def __unicode__(self):
		return self.file_unpacked or self.recover().file_unpacked
		
	class Meta:
		ordering = ('date_commited',)
		get_latest_by = 'date_commited'
