import os
import json

from buildbot.plugins import *

from . import Config

# depends on icperod_setup
from .iceprod_setup import config as iceprod_setup_config

__all__ = ['config']

prefix = __file__.split('/')[-1].rsplit('.',1)[0]

def setup(cfg):

    ####### WORKERS

    cfg['workers'][prefix+'_worker'] = worker.LocalWorker(prefix+'_worker', max_builds=1)


    ####### CHANGESOURCES


    ####### BUILDERS

    path = os.path.abspath('cvmfs')

    factory = util.BuildFactory()
    # start iceprod server
    factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/iceprod.git',
        mode='full',
        method='clobber',
    ))
    factory.addStep(steps.ShellCommand(
        command=[
            '../cvmfs/env/iceprod/master/env-shell.sh',
            'python','-m','integration_tests'
        ],
        locks=[],
    ))

    cfg['builders'][prefix+'_builder'] = util.BuilderConfig(
        name=prefix+'_builder',
        workername=prefix+'_worker',
        factory=factory,
        properties={},
    )


    ####### SCHEDULERS

    cfg['schedulers'][prefix+'-dep'] = schedulers.Triggerable(
        name=prefix+'-dep',
        builderNames=[prefix+'_builder'],
    )

# a fully dependent config
config = None
iceprod_setup_config.register_dependency(Config(setup))
