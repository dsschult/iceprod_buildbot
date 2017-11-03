#!/usr/bin/env python

from __future__ import print_function

import os
import shutil
import tempfile
import subprocess
import time
import json

master_id = ''
workers = {}

d = tempfile.mkdtemp(dir=os.getcwd())
try:
    shutil.copy2('master.cfg',d)
    shutil.copytree('master_cfg_d',os.path.join(d,'master_cfg_d'))
    subprocess.call('chmod g+rwxs '+d,shell=True)

    master_id = subprocess.check_output(['docker','run','-d','--rm',
            '-p','8010:8010',
            '-v',d+':/var/lib/buildbot',
            '--tmpfs','/mnt',
            '-e','WORKER_PASSWORD=pass',
            '-e','BUILDBOT_MASTER_URL=http://localhost:8010/',
            'buildbot/buildbot-master:v0.9.12']).strip()
    time.sleep(.1)
    print('Master started at',master_id[:12])

    # get master ip address
    data = json.loads(subprocess.check_output(['docker','inspect',master_id]))[0]
    master_ip = data['NetworkSettings']['IPAddress']

    for name in os.listdir('docker_images'):
        if name.startswith('worker'):
            name = name.split('-',1)[1]
            w = subprocess.check_output(['docker','run','-d','--rm',
                '--expose','9989',
                '--tmpfs','/iceprod',
                '-e','WORKERPASS=pass',
                '-e','BUILDMASTER='+master_ip,
                '-e','BUILDMASTER_PORT=9989',
                '-e','WORKERNAME='+name,
                'icecube-buildbot/worker-'+name])
            workers[name] = w
            time.sleep(.1)
            print('Worker',name,'started at',w[:12])

    try:
        time.sleep(1000000000000)
    except Exception,KeyboardInterrupt:
        pass

finally:
    print('shutting down')
    try:
        while True:
            change = False
            for line in subprocess.check_output(['docker','ps','--format','{{.ID}}']).split('\n'):
                line = line.strip()
                if not line:
                    continue
                for w_name in workers:
                    if workers[w_name][:12] in line:
                        print('stopping',w_name)
                        subprocess.call(['docker','stop',workers[w_name]],shell=True)
                        time.sleep(.1)
                        change = True
                if master_id[:12] in line:
                    print('stopping master')
                    subprocess.call(['docker','stop',master_id])
                    time.sleep(.1)
                    change = True
            if not change:
                break
    finally:
        shutil.rmtree(d)