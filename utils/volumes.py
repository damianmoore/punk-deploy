import os

import settings
from utils.docker_compose import get_docker_compose_data
from utils.docker_machine import get_machines
from utils.ssh import run_command


def get_volumes(show_un_backed_up=False):
    '''
    Returns the volumes that are mouted in the docker-compose.yml file. Used
    for determining what needs to be synced between machines.
    '''
    volumes = set()

    for item, properties in get_docker_compose_data()['services'].items():
        if 'volumes' in properties:
            for volume_str in properties['volumes']:
                volume = volume_str.split(':')[0]
                volume = volume.replace('/volumes/', '')
                volume = volume.split('/')[0]
                if show_un_backed_up or volume not in settings.NON_BACKED_UP_VOLUMES:
                    volumes.add(volume)

    return sorted(list(volumes))


def sync_volume(volume, src, dst):
    machines = get_machines()

    if src not in machines and src not in ['master']:
        raise KeyError('No source machine called {}'.format(src))
    if dst not in machines and dst not in ['master', 'local']:
        raise KeyError('No destination machine called {}'.format(dst))

    if src == 'master':
        dst_machine = machines[dst]
        cmd = 'rsync -avz {}/{}/ root@{}:/volumes/{}/'.format(settings.MASTER_VOLUMES_PATH, volume, dst_machine['ip'], volume)
        run_command('master', cmd)
    elif dst == 'local':
        src_machine = machines[src]
        cmd = 'rsync -avz root@{}:/volumes/{}/ {}/{}/'.format(src_machine['ip'], volume, os.path.expanduser(settings.LOCAL_VOLUMES_PATH), volume)
        run_command('local', cmd)
    else:
        raise NotImplementedError()
