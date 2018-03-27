import os
import subprocess

import settings
from utils.docker_compose import get_docker_compose_data
from utils.ssh import run_command


def get_private_images():
    '''
    Returns the images referred to in the docker-compose.yml file that get
    built and stored on the private registry.
    '''
    images = set()

    for item, properties in get_docker_compose_data()['services'].items():
        if properties.get('image', '').startswith('{}/'.format(settings.REGISTRY_ADDRESS)):
            images.add(properties['image'].replace('{}/'.format(settings.REGISTRY_ADDRESS), ''))

    return sorted(list(images))


def build_image(image):
    cmd = ['docker', 'build', '-t', '{}/{}'.format(settings.REGISTRY_ADDRESS, image), '{}/{}'.format(os.path.expanduser(settings.LOCAL_REPOS_PATH), image)]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
    except subprocess.CalledProcessError:
        raise RuntimeError('Error building image: {}'.format(' '.join(cmd)))
    if 'Successfully built ' not in output:
        raise RuntimeError('Error building image: {}'.format(' '.join(cmd)))


def push_image(image):
    cmd = ['docker', 'push', '{}/{}'.format(settings.REGISTRY_ADDRESS, image)]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')


def registry_authenticate(machine):
    cmd = 'docker login -u {} -p {} {}'.format(settings.REGISTRY_USER, settings.REGISTRY_PASSWORD, settings.REGISTRY_ADDRESS)
    run_command(machine, cmd, silent=True)
