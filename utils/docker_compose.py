import os
import subprocess

import yaml

import settings
from utils.docker_machine import get_machine


file_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'docker-compose.yml'))


def get_docker_compose_data():
    with open(file_path) as dc:
        data = dc.read()

    return yaml.load(data)


def get_containers():
    return sorted(get_docker_compose_data()['services'].keys())


def launch_docker_compose(machine_name, container=None):
    machine = get_machine(machine_name)
    env_vars = {
        'DOCKER_HOST':          machine['url'],
        'DOCKER_MACHINE_NAME':  machine_name,
        'DOCKER_TLS_VERIFY':    '1',
        'DOCKER_CERT_PATH':     os.path.join(os.path.expanduser(settings.DOCKER_MACHINE_CONFIG_PATH), 'machines', machine_name),
    }

    dc_bin = subprocess.check_output(['which', 'docker-compose'], env=env_vars).decode('utf-8').strip()

    if container:
        commands = [
            [dc_bin, 'pull', container],
            [dc_bin, '-f', file_path, 'kill', container],
            [dc_bin, '-f', file_path, 'rm', '-f', container],
            [dc_bin, '-f', file_path, 'up', '--remove-orphans', '-d'],
        ]
    else:
        commands = [
            [dc_bin, 'pull'],
            [dc_bin, '-f', file_path, 'down'],
            [dc_bin, '-f', file_path, 'up', '--remove-orphans', '-d'],
        ]

    for command in commands:
        subprocess.check_output(command, env=env_vars)
