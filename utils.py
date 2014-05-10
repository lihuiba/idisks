import os, os.path, fnmatch

def logAndCall(func):
	def docall(*arguments, **namedArguments):
        	print "log: %s(*%s, **%s)" %\
                      (func.__name__, arguments, namedArguments)
        	func(*arguments, **namedArguments)
	return docall

def mydir():
	return os.path.dirname(os.path.abspath(__file__))

def _decomposefn(fn):
	i=len(fn)-1
	while i>=0 and '0'<=fn[i] and fn[i]<='9':
		i-=1
	i+=1
	prefix = fn[0:i]
	postfix = fn[i:]
	if len(postfix)>0:
		postfix = int(postfix)
	return (prefix, postfix)

def _fncmp(a,b):
	(a, apostfix) = _decomposefn(a)
	(b, bpostfix) = _decomposefn(b)
	if a<b: return -1
	if a>b: return 1
	return apostfix - bpostfix

def listnodes(pattern):
	ret = os.listdir('.')
	ret = fnmatch.filter(ret, pattern)
	ret = [x for x in ret if os.path.isdir(x)]
	ret.sort(_fncmp)
	return ret

def listdisks():
	ret = os.listdir('.')
	ret = [x for x in ret if os.path.islink(x)]
	ret.sort(_fncmp)
	return ret
