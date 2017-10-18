from __future__ import print_function

import os
import json

from buildbot.plugins import *

from . import Config

__all__ = ['config']

prefix = __file__.split('/')[-1].rsplit('.',1)[0]

def setup(cfg):
    return

    ####### WORKERS

    worker_cfgs = {}
    for name in os.listdir('../config'):
        w_name = name.replace('.json','')
        with open(os.path.join('../config',name)) as f:
            worker_cfgs[w_name] = json.load(f)

    # The 'workers' list defines the set of recognized workers. Each element is
    # a Worker object, specifying a unique worker name and password.  The same
    # worker name and password must be configured on the worker.
    for name in worker_cfgs:
        cfg['workers'][prefix+name] = worker.LocalWorker(
            name, max_builds=1, properties={'image':name}
        )


    ####### CHANGESOURCES


    ####### BUILDERS

    cfg.locks['cvmfs_lock'] = util.MasterLock('cvmfs_lock')

    factory = util.BuildFactory()
    # check out the source
    factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        codebase='cvmfs',
    ))
    factory.addStep(steps.ShellCommand(
        command=self.singularity['cmd']+[
            'python','builders/build.py',
            '--src','icecube.opensciencegrid.org',
            '--dest','/cvmfs/icecube.opensciencegrid.org',
            '--variant',util.Property('variant')
        ],
        locks=[
            cfg.locks['cpu'].access('exclusive'),
            cfg.locks['cvmfs_lock'].access('exclusive'),
        ],
        env=self.singularity['env'],
    ))

    variants = {'py2_v2_base'}

    for v in variants:
        for name in worker_cfgs:
            cfg['builders'][prefix+name+'-'+v] = util.BuilderConfig(
                name=prefix+name+'-'+v,
                workername=prefix+name,
                factory=factory,
                properties={'variant':v},
            )


    ####### SCHEDULERS



config = Config(setup)