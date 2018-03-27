import os
import subprocess

import settings
from utils.docker_machine import get_machine


FNULL = open(os.devnull, 'w')


def run_command(machine_name, command, silent=False, user_key=False):
    stderr = FNULL if silent else None

    address = settings.MASTER_ADDRESS
    if machine_name not in ['master', 'local']:
        address = get_machine(machine_name)['ip']

    if machine_name == 'master' or user_key:
        return subprocess.check_output(['ssh', 'root@{}'.format(address), command], stderr=stderr).decode('utf-8')
    if machine_name == 'local':
        return subprocess.check_output(command.split(' '), stderr=stderr).decode('utf-8')
    else:
        key_file = os.path.join(os.path.expanduser(settings.DOCKER_MACHINE_CONFIG_PATH), 'machines', machine_name, 'id_rsa')
        return subprocess.check_output(['ssh', '-i', key_file, 'root@{}'.format(address), command], stderr=stderr).decode('utf-8')


def get_local_public_key():
    return open(os.path.expanduser('~/.ssh/id_rsa.pub')).read().strip()


def get_machine_public_key(machine_name):
    key_file = os.path.join(os.path.expanduser(settings.DOCKER_MACHINE_CONFIG_PATH), 'machines', machine_name, 'id_rsa.pub')
    return open(key_file).read().strip()


def get_master_public_key():
    return settings.MASTER_PUBLIC_KEY
