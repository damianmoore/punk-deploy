#!/usr/bin/env python
import logging
from time import sleep

from clint.textui import columns, prompt, puts, colored, validators, progress

from utils.databases import get_databases, sync_database_dump, load_database_dump
from utils.docker_compose import launch_docker_compose, get_containers
from utils.docker_images import get_private_images, build_image, push_image
from utils.docker_machine import DRIVERS, get_machines, create_machine, provision_machine, destroy_machine, get_drivers
from utils.initialize import initialize_ssh_keys, initialize_swap, initialize_automatic_updates, initialize_default_apt_packages, initialize_docker_authentication, initialize_volumes
from utils.stats import get_machine_stats
from utils.volumes import get_volumes, sync_volume


LOG_LEVEL = logging.ERROR


def select_machine(message=None, master=False, local=False):
    machines = get_machines()
    machine_options = []
    for i, machine in enumerate(sorted([k for k, v in machines.items() if v['running']])):
        machine_options.append({'selector': str(i + 1), 'prompt': machine, 'return': machine})
    if master:
        i += 1
        machine_options.append({'selector': str(i + 1), 'prompt': 'master', 'return': 'master'})
    if local:
        i += 1
        machine_options.append({'selector': str(i + 1), 'prompt': 'local', 'return': 'local'})

    if not message:
        message = 'Which machine?'
    return prompt.options(colored.yellow('\n{}'.format(message)), machine_options)


def view_machines_prompt():
    machines = get_machines()
    puts('')
    puts(columns([(colored.cyan('Name', bold=True)), 15], [(colored.cyan('Driver')), 15], [(colored.cyan('IP')), 20], [(colored.cyan('Running')), 10], [(colored.cyan('Active')), 10], [(colored.cyan('Uptime')), 15], [(colored.cyan('Load')), 20], [(colored.cyan('Disk')), 25]))
    for name, properties in machines.items():
        machine_stats = get_machine_stats(name)
        puts(columns(
            [name, 15],
            [properties['driver'], 15],
            [properties['ip'], 20],
            [str(properties['running']), 10],
            [str(properties['active']), 10],
            [machine_stats['uptime'], 15],
            [machine_stats['load'], 20],
            [machine_stats['disk'], 25],
        ))
    puts('')


def create_machine_prompt():
    driver_options = []
    for i, driver in enumerate(get_drivers()):
        driver_options.append({'selector': str(i + 1), 'prompt': driver, 'return': driver})
    driver_options.append({'selector': str(len(driver_options) + 1), 'prompt': 'Existing machine', 'return': 'existing'})

    driver = prompt.options(colored.yellow('\nWhich provider?'), driver_options)

    if driver != 'existing':
        driver_config = DRIVERS[driver]

        region = None
        if 'regions' in driver_config:
            region_options = []
            for i, region in enumerate(driver_config['regions']):
                region_options.append({'selector': str(i + 1), 'prompt': '{} - {}'.format(region[0], region[1]), 'return': region[0]})
            region = prompt.options(colored.yellow('\nWhich region?'), region_options)

        size = None
        if 'sizes' in driver_config:
            size_options = []
            for i, size in enumerate(driver_config['sizes']):
                size_options.append({'selector': str(i + 1), 'prompt': '{} - {}'.format(size[0], size[1]), 'return': size[0]})
            size = prompt.options(colored.yellow('\nWhich machine size?'), size_options)

        image = None
        if 'images' in driver_config:
            image_options = []
            for i, image in enumerate(driver_config['images']):
                image_options.append({'selector': str(i + 1), 'prompt': '{} - {}'.format(image[0], image[1]), 'return': image[0]})
            image = prompt.options(colored.yellow('\nWhich machine image?'), image_options)

    name = prompt.query('\nMachine name:', default='', validators=[validators.RegexValidator(r'^[a-z0-9-]{3,20}$', message='3-20 characters, lowercase with hyphens')])

    machines = get_machines()
    if name in machines:
        puts(colored.red('\nMachine {} already exists!\n'.format(name)))
    else:
        if driver == 'existing':
            puts(colored.cyan('\nProvisioning existing machine {}'.format(name)))
            provision_machine(name)
        else:
            puts(colored.cyan('\nCreating new machine {}'.format(name)))
            create_machine(name, driver, region, size, image)
        puts(colored.green('Done!\n'))


def destroy_machine_prompt():
    machine = select_machine()
    sure = prompt.query('\nAre you sure you want to destroy {}? [y/n]:'.format(machine), default='n', validators=[validators.RegexValidator(r'^[yn]$', message='Enter \'y\' or \'n\'')])
    if sure == 'y':
        puts('')
        with progress.Bar(label=colored.cyan('Destroying in... '), expected_size=10, filled_char=colored.red('▮')) as bar:
            for val in sorted(range(11), reverse=True):
                bar.show(val)
                sleep(1)
        puts(colored.cyan('\nDestroying machine {}\n'.format(machine)))
        destroy_machine(machine)
        puts(colored.green('Done!\n'))


def initialize_machine_prompt():
    machine = select_machine()
    tasks = [
        ('ssh keys',        initialize_ssh_keys),
        ('swap',            initialize_swap),
        ('auto update',     initialize_automatic_updates),
        ('apt packages',    initialize_default_apt_packages),
        ('docker auth',     initialize_docker_authentication),
        ('volumes',         initialize_volumes),
    ]
    puts('')
    with progress.Bar(label='{0: <12} '.format(''), expected_size=len(tasks), filled_char=colored.cyan('▮')) as bar:
        for i, (name, function) in enumerate(tasks):
            bar.label = colored.cyan('{0: <12} '.format(name[:12]))
            bar.show(i)
            function(machine)
            bar.show(i)
        bar.label = colored.green('{0: <12} '.format('Done!'))
        bar.show(i)
    puts('')


def build_docker_images():
    images = get_private_images()
    image_options = []
    for i, image in enumerate(images):
        image_options.append({'selector': str(i + 1), 'prompt': image, 'return': image})
    image_options.append({'selector': len(image_options) + 1, 'prompt': '* ALL IMAGES *', 'return': 'all'})
    image = prompt.options(colored.yellow('\nWhich image?'), image_options)

    if image == 'all':
        puts(colored.cyan('\nBuilding {} images\n'.format(len(images))))
        with progress.Bar(label='{0: <12} '.format(''), expected_size=len(images), filled_char=colored.cyan('▮')) as bar:
            val = 0
            for image in images:
                bar.label = colored.cyan('{0: <12} '.format(image[:12]))
                bar.show(val)
                try:
                    build_image(image)
                except Exception as e:
                    puts(colored.red('\n{}\n'.format(e)))
                    exit(1)
                val += 1
                bar.show(val)
            bar.label = colored.green('{0: <12} '.format('Done!'))
            bar.show(val)

        puts(colored.cyan('\nPushing {} images\n'.format(len(images))))
        with progress.Bar(label='{0: <12} '.format(''), expected_size=len(images), filled_char=colored.cyan('▮')) as bar:
            val = 0
            for image in images:
                bar.label = colored.cyan('{0: <12} '.format(image[:12]))
                bar.show(val)
                push_image(image)
                val += 1
                bar.show(val)
            bar.label = colored.green('{0: <12} '.format('Done!'))
            bar.show(val)
        puts('')
    else:
        puts(colored.cyan('\nBuilding {} image'.format(image)))
        try:
            build_image(image)
        except Exception as e:
            puts(colored.red('\n{}\n'.format(e)))
            exit(1)
        puts(colored.green('Done!'))
        puts(colored.cyan('\nPushing {} image'.format(image)))
        push_image(image)
        puts(colored.green('Done!\n'))


def initialize_docker_containers():
    machine = select_machine()

    containers = get_containers()
    container_options = []
    for i, container in enumerate(containers):
        container_options.append({'selector': str(i + 1), 'prompt': container, 'return': container})
    container_options.append({'selector': len(container_options) + 1, 'prompt': '* ALL CONTAINERS *', 'return': 'all'})
    container = prompt.options(colored.yellow('\nWhich container?'), container_options)
    puts('')

    if container == 'all':
        launch_docker_compose(machine)
    else:
        launch_docker_compose(machine, container)
    puts('')


def sync_volumes():
    src_machine = select_machine(message='Which source machine to sync volumes from?', master=True)
    dst_machine = select_machine(message='Which destination machine to sync volumes to?', master=True, local=True)

    if dst_machine == 'local':
        volumes = get_volumes(show_un_backed_up=True)
    else:
        volumes = get_volumes()
    volume_options = []
    for i, volume in enumerate(volumes):
        volume_options.append({'selector': str(i + 1), 'prompt': volume, 'return': volume})
    volume_options.append({'selector': len(volume_options) + 1, 'prompt': '* ALL VOLUMES *', 'return': 'all'})
    volume = prompt.options(colored.yellow('\nWhich volume?'), volume_options)

    if volume == 'all':
        puts(colored.cyan('\nSynchronizing {} volumes from {} to {}\n'.format(len(volumes), src_machine, dst_machine)))
        with progress.Bar(label='{0: <12} '.format(''), expected_size=len(volumes), filled_char=colored.cyan('▮')) as bar:
            for i, volume in enumerate(volumes):
                bar.label = colored.cyan('{0: <12} '.format(volume[:12]))
                bar.show(i)
                sync_volume(volume, src_machine, dst_machine)
            bar.label = colored.green('{0: <12} '.format('Done!'))
            bar.show(i + 1)
        puts('')
    else:
        puts(colored.cyan('\nSynchronizing {} volume from {} to {}'.format(volume, src_machine, dst_machine)))
        sync_volume(volume, src_machine, dst_machine)
        puts(colored.green('Done!\n'))


def sync_databases_from_master():
    databases = get_databases()
    database_options = []
    for i, database in enumerate(databases):
        database_options.append({'selector': str(i + 1), 'prompt': database, 'return': database})
    database_options.append({'selector': len(database_options) + 1, 'prompt': '* ALL DATABASES *', 'return': 'all'})
    database = prompt.options(colored.yellow('\nWhich database?'), database_options)

    machine_selection = select_machine()

    if database == 'all':
        puts(colored.cyan('\nSynchronizing {} databases from master to {}\n'.format(len(databases), machine_selection)))
        with progress.Bar(label='{0: <12} '.format(''), expected_size=len(databases), filled_char=colored.cyan('▮')) as bar:
            for i, database in enumerate(databases):
                bar.label = colored.cyan('{0: <12} '.format(database[:12]))
                bar.show(i)
                sync_database_dump(database, 'master', machine_selection)
                load_database_dump(database, machine_selection)
            bar.label = colored.green('{0: <12} '.format('Done!'))
            bar.show(i + 1)
        puts('')
    else:
        puts(colored.cyan('\nSynchronizing {} database from master to {}'.format(database, machine_selection)))
        sync_database_dump(database, 'master', machine_selection)
        load_database_dump(database, machine_selection)
        puts(colored.green('Done!\n'))


def main():
    logging.root.setLevel(LOG_LEVEL)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    log = logging.getLogger('pythonConfig')
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)

    main_options = [
        {'selector': '1', 'prompt': 'View machines', 'return': view_machines_prompt},
        {'selector': '2', 'prompt': 'Create new machine', 'return': create_machine_prompt},
        {'selector': '3', 'prompt': 'Initialize machine', 'return': initialize_machine_prompt},
        {'selector': '4', 'prompt': 'Build and push docker images', 'return': build_docker_images},
        {'selector': '5', 'prompt': 'Initialize/recreate docker containers', 'return': initialize_docker_containers},
        {'selector': '6', 'prompt': 'Sync volumes', 'return': sync_volumes},
        {'selector': '7', 'prompt': 'Sync databases from master to node', 'return': sync_databases_from_master},
        {'selector': '8', 'prompt': 'Destroy machine', 'return': destroy_machine_prompt},
    ]
    try:
        selection = prompt.options(colored.yellow('\nWhat do you want to do?'), main_options)
        selection()
    except KeyboardInterrupt:
        puts('\n')


if __name__ == '__main__':
    main()
