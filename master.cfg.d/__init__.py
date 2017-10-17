
from buildbot.plugins import *

class WriteOnceDict(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise KeyError('{} has already been set'.format(key))
        super(WriteOnceDict, self).__setitem__(key, value)

class Config(dict):
    """
    A Config object, holding the setup for a BuildBot config.

    Provide a setup function
    """
    def __init__(self, setup=None):
        self['locks'] = WriteOnceDict()
        self['change_source'] = WriteOnceDict()
        self['workers'] = WriteOnceDict()
        self['builders'] = WriteOnceDict()
        self['schedulers'] = WriteOnceDict()

        self.dependencies = []
        self.setup = setup

    def register_dependency(self, dep):
        self.dependencies.append(dep)

    def __call__(self):
        for d in self.dependencies:
            d()
            for k in self:
                self[k].update(d[k])
        dep_sched = [self['schedulers'][s].name for s in self['schedulers'] if self['schedulers'][s].__class__.__name__ == 'Triggerable']
        dep_builders = set(self['builders'])

        self.setup(self)

        # for any new factory made by setup, add dependency trigger
        if dep_sched:
            for b in self['builders']:
                if b not in dep_builders:
                    self['builders'][b].factory.addStep(steps.Trigger(
                        schedulerNames=dep_sched
                    ))
