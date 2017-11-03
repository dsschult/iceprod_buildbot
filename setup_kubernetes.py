#!/usr/bin/env python

from __future__ import print_function

import os
import subprocess
import argparse
from base64 import b64encode
import random
import string
import json
import shutil

import yaml


def randstring(length=12):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def make_secrets():
    # create secrets file
    secrets_path = os.path.join('kubernetes','buildbot-secrets.yml')
    if not os.path.exists(secrets_path):
        with open(secrets_path,'wb') as f:
            yaml.dump({
                'apiVersion':'v1',
                'kind':'Secret',
                'metadata':{
                    'name':'buildbot',
                },
                'data':{
                    'worker_password': b64encode(randstring()),
                },
            }, f, default_flow_style=False)

def make_config():
    # create config file
    config_path = os.path.join('kubernetes','buildbot-config.yml')
    with open(config_path,'wb') as f:
        yaml.dump({
            'apiVersion':'v1',
            'kind':'ConfigMap',
            'metadata':{
                'name':'buildbot-config',
            },
            'data':{
                'worker_password': b64encode(randstring()),
            },
        }, f, default_flow_style=False)

def make_master_cfg():
    # create master.cfg file
    config_path = os.path.join('kubernetes','buildbot-master.cfg.json')
    config = {
        'master.cfg': open('master.cfg').read()
    }
    with open(config_path,'wb') as f:
        json.dump({
            'apiVersion':'v1',
            'kind':'ConfigMap',
            'metadata':{
                'name':'buildbot-master.cfg',
            },
            'data': config,
        }, f, sort_keys=True, indent=4, separators=(',',': '))

    config_path = os.path.join('kubernetes','buildbot-master.cfg.d.json')
    config = {}
    for c in os.listdir('master_cfg_d'):
        if not c.endswith('.py'):
            continue
        name = os.path.join('master_cfg_d',c)
        config[c] = open(name).read()
    with open(config_path,'wb') as f:
        json.dump({
            'apiVersion':'v1',
            'kind':'ConfigMap',
            'metadata':{
                'name':'buildbot-master.cfg.d',
            },
            'data': config,
        }, f, sort_keys=True, indent=4, separators=(',',': '))

def make_docker(name):
    # check if docker image exists
    out = subprocess.check_output(['docker','images',
            '--filter','label=organization=icecube-buildbot',
            '--filter','label=name='+name,
            '--format','{{.Repository}}'])
    if out:
        out = [l for l in out.split('\n') if name in l]
    if not out:
        # build docker image
        docker_path = os.path.join('docker_images',name)
        shutil.copy2('worker_buildbot.tac',
                     os.path.join(docker_path,'buildbot.tac'))
        try:
            subprocess.check_call(['docker','build','--force-rm','-t','icecube-buildbot/'+name,'.'], cwd=docker_path)
        except Exception,KeyboardInterrupt:
            out = subprocess.check_output(['docker','images',
                    '--filter','label=organization=icecube-buildbot',
                    '--filter','label=name='+name,
                    '--format','{{.ID}} {{.Repository}}'])
            if out:
                out = [l for l in out.split('\n') if name not in l]
                subprocess.call(['docker','image','rm',out[0].split()[0]])
            raise
        finally:
            os.remove(os.path.join(docker_path,'buildbot.tac'))

def make_workers():
    for name in os.listdir('docker_images'):
        if not name.startswith('worker'):
            continue

        # make docker image
        make_docker(name)

        # get labels
        container_name = 'icecube-buildbot/'+name
        out = subprocess.check_output(['docker','inspect',container_name])
        config = json.loads(out)[0]['ContainerConfig']
        labels = config['Labels']
        cpus = int(labels['cpus']) if 'cpus' in labels else 1
        gpus = int(labels['gpus']) if 'gpus' in labels else 0
        memory = int(labels['memory']) if 'memory' in labels else 1000
        print(name,'cpus:',cpus,'gpus:',gpus,'memory:',memory)

        # create kubernetes worker json
        kubernetes_path = os.path.join('kubernetes',name+'.json')
        with open(kubernetes_path, 'w') as f:
            json.dump({
                'kind': 'Deployment', 
                'apiVersion': 'apps/v1beta2', 
                'metadata': {
                    'labels': {
                        'app': 'buildbot-worker'
                    }, 
                    'name': name
                },
                'spec': {
                    'replicas': 1,  
                    'selector': {
                        'matchLabels': {
                            'app': 'buildbot-worker'
                        }
                    },
                    'template': {
                        'spec': {
                            'containers': [{
                                'image': container_name,
                                'imagePullPolicy': 'Always',
                                'name': name,
                                'resources': {
                                    'limits': {
                                        'cpu': cpus,
                                        'memory': memory,
                                        'alpha.kubernetes.io/nvidia-gpu': gpus,
                                    },
                                },
                                'env': [
                                    {
                                        'name': 'BUILDMASTER', 
                                        'value': 'buildbot-worker-endpoint',
                                    },{
                                        'name': 'BUILDMASTER_PORT', 
                                        'value': '9989',
                                    },{
                                        'name': 'WORKERNAME',
                                        'value': name.split('-',1)[-1],
                                    },{
                                        'name': 'WORKERPASS',
                                        'valueFrom': {
                                            'secretKeyRef': {
                                                'name': 'buildbot', 
                                                'key': 'worker_password'
                                            }
                                        },
                                    },
                                ],
                                'volumeMounts': [
                                    {
                                        'name': 'iceprod-buildbot-worker-shared-storage',
                                        'mountPath': '/shared',
                                    },
                                ],
                            }],
                            'volumes': [{
                                'name': 'iceprod-buildbot-worker-shared-storage',
                                'persistentVolumeClaim':{
                                    'claimName': 'iceprod-buildbot-worker-pv-claim',
                                },
                            }],
                        }, 
                        'metadata': {
                            'labels': {
                                'app': 'buildbot-worker'
                            }
                        }
                    },
                },
            }, f, sort_keys=True, indent=4, separators=(',',': '))
    

def main():
    parser = argparse.ArgumentParser(description='setup kubernetes')
    args = parser.parse_args()

    make_secrets()
    make_config()
    make_master_cfg()
    make_docker('master-iceprod')
    make_workers()

if __name__ == '__main__':
    main()
