import os
import json

from buildbot.plugins import *

from . import Config

__all__ = ['config']

prefix = __file__.split('/')[-1].rsplit('.',1)[0]

def setup(cfg):

    ####### WORKERS

    cfg['workers'][prefix+'_worker'] = worker.LocalWorker(prefix+'_worker', max_builds=1)


    ####### CHANGESOURCES

    cfg['change_source']['iceprod'] = changes.GitPoller(
        'git://github.com/WIPACrepo/iceprod.git',
        workdir=prefix+'-gitpoller-workdir', branch='master',
        category=prefix, project='iceprod',
        pollinterval=300,
    )


    ####### BUILDERS

    path = os.path.abspath('cvmfs')

    factory = util.BuildFactory()
    # clean everything
    factory.addStep(steps.RemoveDirectory(dir="build"))
    factory.addStep(steps.MakeDirectory(dir="build"))
    factory.addStep(steps.RemoveDirectory(dir=path))
    factory.addStep(steps.MakeDirectory(dir=path))
    # build iceprod
    factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    factory.addStep(steps.ShellCommand(
        command=[
            'python', 'builders/build.py',
            '--src', 'icecube.opensciencegrid.org',
            '--dest', path,
            '--variant', 'iceprod',
            '--version', 'master',
            '--debug',
        ],
        workdir='build',
        locks=[],
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
        include = ['setup.cfg','setup.py','requirements.txt']
        for f in change.files:
            if f in include:
                return True
        return False

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
