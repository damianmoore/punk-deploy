from collections import OrderedDict
import subprocess

import settings


DRIVERS = {
    'digitalocean': {
        'regions': [
            ('ams3', 'Amsterdam 3'),
        ],
        'sizes': [
            ('512mb',   '$5/mo, 1 vCPU, 512MB memory, 20GB SSD'),
            ('1gb',     '$10/mo, 1 vCPU, 1GB memory, 30GB SSD'),
            ('2gb',     '$20/mo, 1 vCPU, 2GB memory, 40GB SSD'),
        ],
        'images': [
            ('ubuntu-16-04-x64', 'Ubuntu 16.04'),
        ],
        'mapping': {
            'token':        'digitalocean-access-token',
            'region':       'digitalocean-region',
            'size':         'digitalocean-size',
            'image':        'digitalocean-image',
        }
    },
    'scaleway': {
        'regions': [
            ('par1', 'Paris'),
            ('ams1', 'Amsterdam'),
        ],
        'sizes': [
            ('VC1S', '€2.99/mo, Virtual 2 x86 64bit cores, 2GB memory, 50GB SSD Disk'),
            ('VC1M', '€5.99/mo, Virtual 4 x86 64bit cores, 4GB memory, 100GB SSD Disk'),
            ('VC1L', '€9.99/mo, Virtual 6 x86 64bit cores, 8GB memory, 200GB SSD Disk'),
            ('C2S', '€11.99/mo, BareMetal 4 x86 64bit cores, 8GB memory, 50GB SSD Disk'),
            ('C2M', '€17.99/mo, BareMetal 8 x86 64bit cores, 16GB memory, 50GB SSD Disk'),
            ('C2L', '€23.99/mo, BareMetal 8 x86 64bit cores, 32GB memory, 50GB SSD Disk + 250GB Direct SSD Disk'),
        ],
        'images': [
            ('ubuntu-xenial', 'Ubuntu 16.04'),
        ],
        'mapping': {
            'token':        'scaleway-token',
            'access_key':   'scaleway-organization',
            'name':         'scaleway-name',
            'region':       'scaleway-region',
            'size':         'scaleway-commercial-type',
            'image':        'scaleway-image',
        }
    }
}
machines = None


def get_machines():
    global machines

    if machines:
        # Use cached value if this function was previously called
        return machines
    try:
        output = subprocess.check_output(['docker-machine', 'ls'], stderr=subprocess.STDOUT).decode('utf-8')
        machines = {}

        for line in output.split('\n'):
            if not line.startswith('NAME') and not line.startswith('error '):
                fields = line.split()
                if len(fields) < 2:
                    continue

                machine = {
                    'active': False,
                    'running': False,
                }

                if fields[1] == '*':
                    machine['active'] = True

                machine['driver'] = fields[2]
                if fields[3] == 'Running':
                    machine['running'] = True
                machine['url'] = fields[4]

                if machine['url']:
                    machine['ip'] = machine['url'].split('://')[1].split(':')[0]

                machines[fields[0]] = machine

    except IndexError:
        return get_machines()

    return OrderedDict(sorted(machines.items()))


def get_machine(name):
    return get_machines()[name]


def create_machine(name, driver, region=None, size=None, image=None):
    cmd = ['docker-machine', 'create', '-d', driver]

    driver_config = DRIVERS[driver]
    mapping = driver_config['mapping']

    cmd += ['--{}'.format(mapping['token']), getattr(settings, '{}_TOKEN'.format(driver.upper()))]
    if 'access_key' in mapping:
        cmd += ['--{}'.format(mapping['access_key']), getattr(settings, '{}_ACCESS_KEY'.format(driver.upper()))]
    if 'name' in mapping:
        cmd += ['--{}'.format(mapping['name']), name]

    if region:
        cmd += ['--{}'.format(mapping['region']), region]
    if size:
        cmd += ['--{}'.format(mapping['size']), size]
    if image:
        cmd += ['--{}'.format(mapping['image']), image]

    cmd += [name]
    print(' '.join(cmd))
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def provision_machine(name):
    # TODO: implement!
    pass


def destroy_machine(name):
    cmd = ['docker-machine', 'rm', '-y', name]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def get_drivers():
    drivers = []
    for driver in ['digitalocean', 'scaleway']:
        if getattr(settings, '{}_TOKEN'.format(driver.upper())):
            drivers.append(driver)
    return drivers
