from __future__ import print_function

import os
import json

from buildbot.plugins import *

from . import Config, get_os


prefix = __file__.split('/')[-1].rsplit('.',1)[0]


def setup(cfg):

    ####### WORKERS

    workername = 'iceprod-centos7-build'
    cfg['workers'][workername] = worker.Worker(
        workername, os.environ['WORKER_PASSWORD'],
        max_builds=1,
    )


    ####### CHANGESOURCES

    cfg['change_source']['iceprod'] = changes.GitPoller(
        'git://github.com/WIPACrepo/iceprod.git',
        workdir=prefix+'-iceprod-gitpoller-workdir', branch='master',
        category=prefix,
        pollinterval=300,
    )

    ####### BUILDERS

    path = '/shared/iceprod'

    factory = util.BuildFactory()
    # clean everything
    factory.addStep(steps.RemoveDirectory(name='clean build', dir="build"))
    factory.addStep(steps.MakeDirectory(name='mkdir build', dir="build"))
    factory.addStep(steps.RemoveDirectory(name='clean cvmfs', dir=path))
    factory.addStep(steps.MakeDirectory(name='mkdir cvmfs', dir=path))
    # build iceprod
    factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    factory.addStep(steps.ShellCommand(
        name='build cvmfs',
        command=[
            'python', 'builders/build.py',
            '--src', 'icecube.opensciencegrid.org',
            '--dest', path,
            '--variant', 'iceprod',
            '--version', 'master',
            '--debug',
        ],
        workdir='build',
        haltOnFailure=True,
        locks=[
            cfg.locks['iceprod_shared'].access('exclusive')
        ],
    ))

    cfg['builders'][prefix+'_builder'] = util.BuilderConfig(
        name=prefix+'_builder',
        workername=workername,
        factory=factory,
        properties={},
    )

    nonbuild_factory = util.BuildFactory()
    cfg['builders'][prefix+'_nonbuild_builder'] = util.BuilderConfig(
        name=prefix+'_nonbuild_builder',
        workername=workername,
        factory=nonbuild_factory,
        properties={},
    )


    ####### SCHEDULERS

    def isImportant(change):
        try:
            if not os.listdir(path):
                return True # needs rebuilding
            include = ['setup.cfg','setup.py','requirements.txt']
            for f in change.files:
                if f in include:
                    return True
            return False
        except:
            return True

    cfg['schedulers'][prefix] = schedulers.SingleBranchScheduler(
        name=prefix,
        change_filter=util.ChangeFilter(category=prefix),
        fileIsImportant=isImportant,
        treeStableTimer=None,
        builderNames=[prefix+'_builder'],
    )
    cfg['schedulers']['iceprod'] = schedulers.SingleBranchScheduler(
        name='iceprod',
        change_filter=util.ChangeFilter(category=prefix),
        fileIsImportant=lambda x:not isImportant(x),
        treeStableTimer=None,
        builderNames=[prefix+'_nonbuild_builder'],
    )

config = Config(setup)
config.locks['iceprod_shared'] = util.MasterLock('cvmfs_lock')
