from __future__ import print_function

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

    cfg['workers'][prefix+'_worker'] = worker.LocalWorker(
        prefix+'_worker', max_builds=1,
        #properties={'image': 'cvmfs_centos7'}, # singularity image
    )


    ####### CHANGESOURCES


    ####### BUILDERS

    cvmfs_path = os.path.abspath('cvmfs')
    coverage_path = os.path.abspath('coverage')

    factory = util.BuildFactory()
    # start iceprod server
    factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/iceprod.git',
        mode='full',
        method='clobber',
        codebase='iceprod',
    ))
    factory.addStep(steps.ShellCommand(
        name='unittest',
        command=[
            os.path.join(cvmfs_path,'iceprod/master/env-shell.sh'),
            './coverage.sh','--core','--server',
        ],
        locks=[
            cfg.locks['cpu'].access('counting'),
        ],
    ))
    factory.addStep(steps.ShellSequence(
        name='coverage',
        commands=[
            util.ShellArg(command=['cp','-r','htmlcov',coverage_path+'.tmp']),
            util.ShellArg(command=['mv',coverage_path+'.tmp',coverage_path]),
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
        codebases=['iceprod'],
        builderNames=[prefix+'_builder'],
    )

# a fully dependent config
config = None
iceprod_setup_config.register_dependency(Config(setup))
