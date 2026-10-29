"""Exact grammar for the solver's text tool calls; a call is recognized only when it matches completely.

Part of harness/runtime/self: the practice harness for learning from feedback alone (self)."""
import json,re
BLOCK=re.compile(r'<(function-call|tool_call)>(.*?)</\1>',re.S)
def parse_text_calls(content,allowed,start=0):
 text=(content or '').strip(); blocks=list(BLOCK.finditer(text));pos=0;out=[]
 if not blocks:return None
 for block in blocks:
  if text[pos:block.start()].strip():return None
  pos=block.end()
  try:
   obj=json.loads(block.group(2))
   if not isinstance(obj,dict) or obj.get('name') not in allowed:return None
   args=obj.get('arguments')
   if isinstance(args,str):args=json.loads(args)
   if not isinstance(args,dict):return None
  except (ValueError,TypeError):return None
  out.append(dict(id=f'textcall-{start+len(out)+1}',type='function',function=dict(name=obj['name'],arguments=json.dumps(args,ensure_ascii=False,separators=(',',':')))))
 if text[pos:].strip():return None
 return out
def unwrap_function(content):
 text=(content or '').strip();match=re.fullmatch(r'<function>(.*?)</function>',text,re.S)
 if not match:return content
 inner=match.group(1)
 try:obj=json.loads(inner)
 except ValueError:obj=None
 if isinstance(obj,dict) and 'name' in obj:return content
 return inner
