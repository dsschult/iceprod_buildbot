from __future__ import print_function

import os
import json

from buildbot.plugins import *

from . import Config

__all__ = ['config']

prefix = __file__.split('/')[-1].rsplit('.',1)[0]

def setup(cfg):

    ####### WORKERS

    cfg['workers'][prefix+'_worker'] = worker.LocalWorker(
        prefix+'_worker', max_builds=1,
        #properties={'image': 'cvmfs_centos7'}, # singularity image
    )


    ####### CHANGESOURCES

    cfg['change_source']['iceprod'] = changes.GitPoller(
        'git://github.com/WIPACrepo/iceprod.git',
        workdir=prefix+'-iceprod-gitpoller-workdir', branch='master',
        category=prefix, project='iceprod',
        pollinterval=300,
    )
    cfg.codebases['iceprod'] = 'git://github.com/WIPACrepo/iceprod.git'

    cfg['change_source']['cvmfs'] = changes.GitPoller(
        'git://github.com/WIPACrepo/cvmfs.git',
        workdir=prefix+'-cvmfs-gitpoller-workdir', branch='master',
        category=prefix, project='cvmfs',
        pollinterval=300,
    )
    cfg.codebases['cvmfs'] = 'git://github.com/WIPACrepo/cvmfs.git'


    ####### BUILDERS

    path = os.path.abspath('cvmfs')

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
            cfg.locks['cpu'].access('exclusive'),
        ],
    ))

    cfg['builders'][prefix+'_builder'] = util.BuilderConfig(
        name=prefix+'_builder',
        workername=prefix+'_worker',
        factory=factory,
        properties={},
    )

    nonbuild_factory = util.BuildFactory()
    cfg['builders'][prefix+'_nonbuild_builder'] = util.BuilderConfig(
        name=prefix+'_nonbuild_builder',
        workername=prefix+'_worker',
        factory=nonbuild_factory,
        properties={},
    )


    ####### SCHEDULERS

    def isImportant(change):
        if change.project == 'cvmfs':
            include = ['iceprod']
        elif change.project == 'iceprod':
            include = ['setup.cfg','setup.py','requirements.txt']
        else:
            return True
        for f in change.files:
            if f in include:
                return True
        return False

    cfg['schedulers'][prefix] = schedulers.SingleBranchScheduler(
        name=prefix,
        change_filter=util.ChangeFilter(category=prefix),
        codebases=['iceprod','cvmfs'],
        fileIsImportant=isImportant,
        treeStableTimer=None,
        builderNames=[prefix+'_builder'],
    )
    cfg['schedulers']['iceprod'] = schedulers.SingleBranchScheduler(
        name='iceprod',
        change_filter=util.ChangeFilter(category=prefix),
        codebases=['iceprod','cvmfs'],
        fileIsImportant=lambda x:not isImportant(x),
        treeStableTimer=None,
        builderNames=[prefix+'_nonbuild_builder'],
    )

config = Config(setup)
