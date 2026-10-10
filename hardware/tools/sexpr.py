"""Small deterministic S-expression reader/writer for KiCad source generation."""
import re,json
class Atom(str):pass
def parse(s):
 t=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s);i=0
 def one():
  nonlocal i
  q=t[i];i+=1
  if q=='(':
   a=[]
   while t[i]!=')':a.append(one())
   i+=1;return a
  if q.startswith('"'):return json.loads(q)
  return Atom(q)
 return one()
def dump(a):
 if isinstance(a,list):return '('+' '.join(dump(x) for x in a)+')'
 if isinstance(a,Atom):return str(a)
 if isinstance(a,str):return json.dumps(a)
 return str(a)
def children(a,key):return [x for x in a if isinstance(x,list) and x and x[0]==key]
def child(a,key,default=None):return next(iter(children(a,key)),default)
def atom(s):return Atom(str(s))
