import os.path, subprocess, re

class tgtadm:
	_target=None
	_targets={}
	_lun=None
	_iqn_prefix="iqn.2014-05.idisks:node."
	def __init__(self):
		self.load_targets_luns()
	def load_targets_luns(self):
		self._targets={}
		self._target=None
		self._lun=None
		iqnprefix = self._iqn_prefix.replace('.', "\\.")
		ptarget = ('Target ', re.compile("(\\d*): {0}(.*)".format(iqnprefix)), self._meet_target )
		plun =    ('        LUN: ', re.compile("(\d*)"), self._meet_lun)
		pstore =  ('            Backing store path: ', re.compile("(.*)"), self._meet_store)
		patterns = (ptarget, plun, pstore)
		p=subprocess.Popen('tgt-admin -s', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		for line in p.stdout:
			for p in patterns:
				if not line.startswith(p[0]):
					continue
				line = line[len(p[0]):]
				m=p[1].match(line)
				if not m:
					continue
				p[2](m.groups())
	def _meet_target(self, m):
		node = m[1]
		target = int(m[0])
		if not target in self._targets:
			self._targets[target] = {'index':target, 'node': node}
		self._target = self._targets[target]
	def _meet_lun(self, m):
		lun = int(m[0])
		target = self._target
		if not target:
			return
		if not lun in target:
			target[lun] = {'index': lun, 'tid': target['index']}
		self._lun = target[lun]
	def _meet_store(self, m):
		if not self._lun:
			return
		store=m[0]
		if store!='None':
			self._lun['store'] = store
		else:
			del self._target[self._lun['index']]
			self._lun = None

	@staticmethod
	def iterator(x):
		for key in x:
			if type(key) is int:
				yield x[key]
	@staticmethod
	def get_available_id(container):
		xid=1
		while xid in container:
			xid+=1
		return xid
	def lookup_lun_by_store_iter(self, store):
		store = os.path.realpath(store)
		for target in self.iterator(self._targets):
			for lun in self.iterator(target):
				lstore = os.path.realpath(lun.get('store'))
				if lstore==store:
					yield lun
	def lookup_lun_by_store(self, store):
		for x in self.lookup_lun_by_store_iter(store):
			return x
	def lookup_luns_by_store(self, store):
		return [x for x in self.lookup_lun_by_store_iter(store)]
	@staticmethod
	def get_luns(target):
		return [key for key in target if type(key) is int]
	def lookup_target_by_node(self, node):
		for target in self.iterator(self._targets):
			if target.get('node')==node:
				return target
	def create_target(self, node):
		assert not self.lookup_target_by_node(node)
		tid = self.get_available_id(self._targets)
		cmd = "tgtadm --lld iscsi --mode target --op new --tid {0} --targetname {1}{2}"
		cmd = cmd.format(tid, self._iqn_prefix, node)
		p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdoutdata, stderrdata) = p.communicate()
		self.load_targets_luns()
		assert tid in self._targets, "{0}\n{1}\n{2}".format(cmd, stdoutdata, stderrdata)
		return self._targets[tid]
	def delete_target(self, node):
		target = self.lookup_target_by_node(node)
		assert target
		tid = target['index']
		cmd = "tgtadm --lld iscsi --mode target --op delete --tid {0}"
		cmd = cmd.format(tid)
		p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdoutdata, stderrdata) = p.communicate()
		self.load_targets_luns()
		assert not tid in self._targets, "{0}\n{1}\n{2}".format(cmd, stdoutdata, stderrdata)
		return tid
	@staticmethod
	def copy_dict(dest, src):
		dest.clear()
		for key in src:
			dest[key] = src[key]
	def create_lun(self, target, lun, store):
		assert type(lun) is int
		assert not target.get(lun)
		tid = target['index']
		cmd = "tgtadm --lld iscsi --mode logicalunit --op new --tid {0} --lun {1} --backing-store {2}"
		cmd = cmd.format(tid, lun, store)
		# print cmd
		p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdoutdata, stderrdata) = p.communicate()
		self.load_targets_luns()
		new_target = self._targets[tid]
		self.copy_dict(target, new_target)
		assert target.get(lun), "{0}\n{1}\n{2}".format(cmd, stdoutdata, stderrdata)
		return target[lun]
	def delete_lun(self, target, lun):
		assert type(lun) is int
		assert target.get(lun)
		tid = target['index']
		cmd = "tgtadm --lld iscsi --mode logicalunit --op delete --tid {0} --lun {1}"
		cmd = cmd.format(tid, lun)
		# print cmd
		p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdoutdata, stderrdata) = p.communicate()
		self.load_targets_luns()
		new_target = self._targets[tid]
		self.copy_dict(target, new_target)
		assert not target.get(lun), "{0}\n{1}\n{2}".format(cmd, stdoutdata, stderrdata)
		return lun
