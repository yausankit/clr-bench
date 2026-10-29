"""Tool-using solver shared by all methods. It reads the task prompt, the system prompt built from the learned state
(common.persona), and returns one program; the same solver writes practice and test programs.

Part of harness/runtime/self: the practice harness for learning from feedback alone (self)."""
import copy
import json
import os
from pathlib import Path
from common import dump,compact,persona
from text_calls import parse_text_calls,unwrap_function
from transport import completion,ModelTransportError
from evolution_curriculum.client import Client,RemoteError


class Native:
    def __init__(self,client,root):self.client,self.root,self.serial=client,Path(root),0
    def call(self,ctx,role,prompt,system,kind='execute',files=None,workspace=None,response_format=None):
        self.serial+=1;folder=self.root/'calls'/f'{self.serial:05d}-{role}'
        messages=[dict(role='system',content=system),dict(role='user',content=prompt)]
        definitions=[];submitted=None;observations=[];text_serial=0;text_parse_failures=[];feedback_rounds=[];final_checks=[]
        task_id=ctx.get('task_id',f"{ctx['sample']}.L{ctx['level']}.evaluation")
        current=self.client.tools(task_id)
        if kind=='execute':definitions.extend(current.definitions)
        def define(n,d,props,required):definitions.append(dict(name=n,description=d,parameters=dict(type='object',properties=props,required=required)))
        if files:
            define('read_skill','Read a file from the learned skill directory.',{'path':{'type':'string'}},['path'])
            define('run_skill','Execute a learned Python helper run(data,args) on current full raw input.',{'path':{'type':'string'},'args':{'type':'object'}},['path','args'])
        if workspace is not None:
            define('read_file','Read a current Wiki/Skill/trace workspace file.',{'path':{'type':'string'}},['path'])
            define('finish','Submit one skill proposal.',{'proposal':{'type':'object'}},['proposal'])
        tools=[dict(type='function',function=d) for d in definitions]
        dump(folder/'INPUT.json',dict(context=ctx,role=role,messages=messages,tools=tools,response_format=response_format))
        if os.environ.get('PB4_DRY_RUN') == '1':
            result=dict(text='def solve(data):\n    return 0',folder=str(folder),submitted_proposal=None,text_parse_failures=[],execution_feedback_rounds=[],final_example_observations=[])
            dump(folder/'MESSAGES.json',messages);dump(folder/'RESULT.json',result)
            return result
        os.environ['RSI_CONTEXT']=f"{ctx['method']}/{ctx['sample']}/L{ctx['level']}/{ctx.get('phase',role)}/{self.serial}"
        for step in range(41):
            response,messages=completion(messages,tools=tools,label=role,response_format=response_format)
            msg=copy.deepcopy(response['choices'][0]['message']);msg.pop('reasoning_content',None);messages.append(msg)
            dump(folder/f'response-{step:03d}.json',response)
            calls=msg.get('tool_calls',[])
            if not calls:
                calls=parse_text_calls(msg.get('content'),{d['name'] for d in definitions},text_serial)
                if calls:
                    text_serial+=len(calls);msg['tool_calls']=calls
                else:
                    if '<function-call>' in (msg.get('content') or '') or '<tool_call>' in (msg.get('content') or ''):
                        text_parse_failures.append(dict(step=step,content=msg.get('content')))
                    msg['content']=unwrap_function(msg.get('content'))
                    if role=='solve' and kind=='execute':
                        observation=current.run_candidate(code=msg['content'])
                        final_checks.append(observation)
                        if observation.get('ok') is False and len(feedback_rounds)<2:
                            error=observation.get('error','')
                            feedback='Your final program failed on the example input with this error: '+error+'. Fix the program and submit the full corrected program, which must define solve(...) and return an int, as your final assistant message.'
                            feedback_rounds.append(dict(round=len(feedback_rounds)+1,error=error,message=feedback))
                            messages.append(dict(role='user',content=feedback))
                            continue
                    break
            if step==40:
                msg=dict(content='Solver tool-round budget exhausted without a final artifact');break
            for call in calls:
                name=call['function']['name']
                original_args=call['function']['arguments']
                try:
                    args=json.loads(original_args)
                    if not isinstance(args,dict): raise ValueError('Tool arguments must be an object')
                except (ValueError,TypeError) as e:
                    # Do not send an invalid assistant function-call object to the provider.
                    # Keep valid sibling calls, record the rejected call verbatim as text.
                    msg['tool_calls']=[c for c in msg['tool_calls'] if c['id']!=call['id']]
                    msg['content']=(msg.get('content') or '')+'\nRejected malformed tool call: '+compact(call)
                    observations.append(dict(name=name,args=original_args,result={'error':str(e),'executed':False}))
                    continue
                try:
                    if name=='inspect_source':result=current.inspect_source(**args)
                    elif name=='run_candidate':result=current.run_candidate(**args)
                    elif name=='read_skill':result=files[args['path']]
                    elif name=='read_file':result=workspace[args['path']]
                    elif name=='finish':submitted=args['proposal'];result={'submitted':True}
                    elif name=='run_skill':
                        from bridge import invoke
                        # Obtain exactly the current public raw source through the same interface.
                        data=current.public_input()
                        result=invoke(folder/f'skill-{step}-{len(observations)}',files,args['path'],'run',[data,args.get('args',{})])
                    else:raise ValueError('Unknown tool')
                except (ValueError,KeyError,TypeError) as e:result=dict(error=str(e))
                observations.append(dict(name=name,args=call['function']['arguments'],result=result,call_format='text' if call['id'].startswith('textcall-') else 'native',call_id=call['id']))
                messages.append(dict(role='tool',tool_call_id=call['id'],content=compact(result)))
            if not msg.get('tool_calls'):
                msg.pop('tool_calls',None)
                messages.append(dict(role='user',content='The preceding malformed tool call was not executed. Reissue it with a valid JSON object, or submit your final answer.'))
            if submitted is not None:
                msg=dict(content=compact(submitted));break
        result=dict(text=msg.get('content') or '',folder=str(folder),submitted_proposal=submitted,text_parse_failures=text_parse_failures,execution_feedback_rounds=feedback_rounds,final_example_observations=final_checks)
        dump(folder/'MESSAGES.json',messages);dump(folder/'TOOLS.json',observations);dump(folder/'RESULT.json',result)
        return result


def solve(native,ctx,state,folder):
    task,=native.client.tasks(task_id=ctx.get('task_id',f"{ctx['sample']}.L{ctx['level']}.evaluation"))
    dump(Path(folder)/'STATE_USED.json',state)
    result=native.call(ctx,'solve',task['prompt'],persona(task,ctx['method'],state),files=state.get('files'))
    return task,result


def solve_grade(native,ctx,state,folder):
    task,result=solve(native,ctx,state,folder);feedback=native.client.feedback(task['task_id'],result['text'])
    trace=dict(task_prompt=task['prompt'],assistant_final=result['text'],feedback=feedback,reference_solution_provided=False,split=ctx['split'])
    dump(Path(folder)/'GRADE.json',feedback);dump(Path(folder)/'TRACE.json',trace)
    return feedback,trace


def develop(native,method,sid,level,state,folder):
    rows=[solve_grade(native,dict(method=method,sample=sid,level=level,phase='development',split=f'validation{i}'),state,Path(folder)/f'v{i}') for i in (1,2)]
    return [r[0]['pass_'] for r in rows],[r[1] for r in rows]
