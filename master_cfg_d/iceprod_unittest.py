from __future__ import print_function

import os
import json

from buildbot.plugins import *

from . import Config, get_os

# depends on icperod_setup
from .iceprod_setup import config as iceprod_setup_config


prefix = __file__.split('/')[-1].rsplit('.',1)[0]


def setup(cfg):

    ####### WORKERS

    workername = 'iceprod-centos7'
    cfg['workers'][workername] = worker.Worker(
        workername, os.environ['WORKER_PASSWORD'],
        max_builds=1,
    )


    ####### CHANGESOURCES


    ####### BUILDERS

    cvmfs_path = '/shared/iceprod'
    coverage_path = '/shared/coverage'

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
        ],
    ))
    factory.addStep(steps.ShellSequence(
        name='coverage',
        commands=[
            util.ShellArg(command=['cp','-r','htmlcov',coverage_path+'.tmp']),
            util.ShellArg(command=['mv',coverage_path+'.tmp',coverage_path]),
        ],
        locks=[
        ],
    ))

    cfg['builders'][prefix+'_builder'] = util.BuilderConfig(
        name=prefix+'_builder',
        workername=workername,
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
