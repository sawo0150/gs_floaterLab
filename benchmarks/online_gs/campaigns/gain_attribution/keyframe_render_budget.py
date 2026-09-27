"""Diagnostic work budget: 15 differentiable camera renders per admitted KF.

Instance-scoped wrapper; no production defaults, loss, topology policy or
observation data are changed. Native work gets at most one multi-view step per
arrival; unused credit goes to the original additional trainer.
"""
import inspect
from types import MethodType

class KeyframeRenderBudget:
    def __init__(self, mapper, audit, renders_per_kf=15):
        if renders_per_kf<1:raise ValueError('Positive budget required')
        self.mapper,self.audit=mapper,audit
        self.renders_per_kf=renders_per_kf
        self.seen=set();self.admissions=[];self.native_calls=[]
        self.arrival_uid=None;self.native_called=False
        original=mapper.map
        signature=inspect.signature(original)
        def budgeted(instance,*args,**kwargs):
            bound=signature.bind(*args,**kwargs);bound.apply_defaults()
            if bound.arguments.get('photometric_only',False):return original(*args,**kwargs)
            self.sync()
            remaining=self.target-audit.training
            if remaining<0:raise RuntimeError('Native render budget exceeded')
            if self.native_called or remaining==0 or bound.arguments['iters']<=0:return 0
            self.native_called=True
            requested=bound.arguments['iters']
            bound.arguments['iters']=1
            bound.arguments['max_viewpoints']=min(bound.arguments['max_viewpoints'],remaining)
            before=audit.training
            result=original(*bound.args,**bound.kwargs)
            self.native_calls.append({'arrival_uid':self.arrival_uid,'requested_iters':requested,
                'max_viewpoints':bound.arguments['max_viewpoints'],'renders':audit.training-before,
                'remaining_before':remaining})
            if audit.training>self.target:raise RuntimeError('Native call exceeded render credit')
            return result
        mapper.map=MethodType(budgeted,mapper)

    def start_arrival(self,uid):
        self.arrival_uid=int(uid);self.native_called=False

    def sync(self):
        generation=self.mapper.online_view_trainer.generation
        for uid,view in sorted(self.mapper.viewpoints.items()):
            if getattr(view,'mapping_eval_excluded',False):continue
            key=(generation,int(uid))
            if key not in self.seen:
                self.seen.add(key)
                self.admissions.append({'generation':generation,'uid':int(uid),
                    'arrival_uid':self.arrival_uid,'renders':self.renders_per_kf})

    @property
    def target(self):return self.renders_per_kf*len(self.seen)

    def report(self):
        return {'renders_per_kf':self.renders_per_kf,'kf_admissions':len(self.seen),
                'distinct_kf_uids':len({u for _,u in self.seen}),'target':self.target,
                'admissions':self.admissions,'native_calls':self.native_calls,
                'reset_rule':'KF re-admission in a new map generation earns new credit'}
