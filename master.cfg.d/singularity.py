import os
import json

from buildbot.plugins import *

__all__ = ['workers', 'change_source', 'builders', 'schedulers']


####### WORKERS

worker_cfgs = {}
for name in os.listdir('../config'):
    w_name = name.replace('.json','')
    with open(os.path.join('../config',name)) as f:
        worker_cfgs[w_name] = json.load(f)

# The 'workers' list defines the set of recognized workers. Each element is
# a Worker object, specifying a unique worker name and password.  The same
# worker name and password must be configured on the worker.
workers = []
for name in worker_cfgs:
    w = worker.LocalWorker(name, max_builds=1, properties={'image':name})
    workers.append(w)


####### CHANGESOURCES

# the 'change_source' setting tells the buildmaster how it should find out
# about source code changes.  Here we point to the buildbot clone of pyflakes.

change_source = []
#change_source.append(changes.GitPoller(
#        'git://github.com/buildbot/pyflakes.git',
#        workdir='gitpoller-workdir', branch='master',
#        pollinterval=300))


####### Singularity Builders

# The 'builders' list defines the Builders, which tell Buildbot how to perform a build:
# what steps, and which workers can execute them.  Note that any particular build will
# only take place on one worker.

img_path = os.path.abspath('../singularity_images')
singularity_cmd = ['singularity','exec','-B','/mnt/build:/cvmfs',
                   util.Interpolate(img_path+'/%(prop:image)s.img')]

build_lock = util.MasterLock('build')

path_override = '/usr/local/bin:/usr/bin:/bin:/bin:/sbin:/usr/bin:/usr/sbin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'

factory = util.BuildFactory()
# check out the source
factory.addStep(steps.Git(repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full', method='clobber'))
factory.addStep(steps.ShellCommand(
    command=singularity_cmd+[
        'python','builders/build.py',
        '--src','icecube.opensciencegrid.org',
        '--dest','/cvmfs/icecube.opensciencegrid.org',
        '--variant',util.Property('variant')
    ],
    env={'PATH':path_override},
    locks=[build_lock.access('exclusive')],
))

variants = {'py2_v2_base'}

builders = []
for v in variants:
    for name in worker_cfgs:
        builders.append(util.BuilderConfig(
            name=name+'-'+v,
            workername=name,
            factory=factory,
            properties={'variant':v},
        ))


####### SCHEDULERS

# Configure the Schedulers, which decide how to react to incoming changes.

schedulers = []
#schedulers.append(schedulers.SingleBranchScheduler(
#                            name="all",
#                            change_filter=util.ChangeFilter(branch='master'),
#                            treeStableTimer=None,
#                            builderNames=["runtests"]))
