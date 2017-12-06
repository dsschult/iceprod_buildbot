from __future__ import print_function

import os
import json

from buildbot.plugins import *
from buildbot.process.buildstep import SUCCESS,SKIPPED

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

    def isImportant(change):
        try:
            if not (os.path.exists(path) and os.listdir(path)):
                return True # needs rebuilding
            include = ['setup.cfg','setup.py','requirements.txt']
            for f in change.files:
                if f in include:
                    return True
            return False
        except:
            raise
            return True

    class SetupCVMFS(steps.BuildStep):
        def run(self):
            changes = util.Properties('changes')
            if isImportant(changes):
                # create a ShellCommand for each stage and add them to the build
                self.build.addStepsAfterCurrentStep([
                    steps.RemoveDirectory(name='clean build', dir="build"),
                    steps.MakeDirectory(name='mkdir build', dir="build"),
                    steps.RemoveDirectory(name='clean cvmfs', dir=path),
                    steps.MakeDirectory(name='mkdir cvmfs', dir=path),
                    # build iceprod
                    steps.Git(
                        repourl='git://github.com/WIPACrepo/cvmfs.git',
                        mode='full',
                        method='clobber',
                        workdir='build',
                    ),
                    steps.ShellCommand(
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
                    ),
                ])
                return SUCCESS
            return SKIPPED


    factory = util.BuildFactory()
    factory.addStep(SetupCVMFS(
        name="Do setup?",
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


    ####### SCHEDULERS

    cfg['schedulers'][prefix] = schedulers.SingleBranchScheduler(
        name=prefix,
        change_filter=util.ChangeFilter(category=prefix),
        treeStableTimer=None,
        builderNames=[prefix+'_builder'],
    )

config = Config(setup)
config.locks['iceprod_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
