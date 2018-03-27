import subprocess

from utils.docker_machine import get_machine
from utils.docker_images import registry_authenticate
from utils.ssh import run_command, get_local_public_key, get_master_public_key


def initialize_ssh_keys(machine_name):
    try:
        run_command(machine_name, 'pwd', silent=True, user_key=True)
    except subprocess.CalledProcessError:
        cmd = 'echo "{}" >> /root/.ssh/authorized_keys'.format(get_local_public_key())
        run_command(machine_name, cmd)

    machine = get_machine(machine_name)
    try:
        cmd = 'ssh root@{} pwd'.format(machine['ip'])
        run_command('master', cmd, silent=True, user_key=True)
    except subprocess.CalledProcessError:
        # Authorize master to login to new machine
        master_public_key = get_master_public_key()
        cmd = 'echo "{}" >> /root/.ssh/authorized_keys'.format(master_public_key)
        run_command(machine_name, cmd)

        # Add host public key to master so it trusts the connection
        cmd = 'cat /etc/ssh/ssh_host_rsa_key.pub'
        machine_host_public_key = run_command(machine_name, cmd)
        cmd = 'echo "{} {}" >> /root/.ssh/known_hosts'.format(machine['ip'], machine_host_public_key)
        run_command('master', cmd)


def initialize_swap(machine):
    if '/swapfile' not in run_command(machine, 'cat /proc/swaps'):
        cmd = 'dd if=/dev/zero of=/swapfile bs=1024 count=4096k &&\
            mkswap /swapfile &&\
            chmod 600 /swapfile &&\
            swapon /swapfile &&\
            echo "/swapfile swap swap defaults 0 0" >> /etc/fstab'
        run_command(machine, cmd, silent=True)


def initialize_automatic_updates(machine):
    if 'Unattended-Upgrade' not in run_command(machine, 'cat /etc/apt/apt.conf.d/10periodic'):
        cmd = 'apt-get update &&\
            apt-get install unattended-upgrades &&\
            echo APT::Periodic::Unattended-Upgrade "1"\; >> /etc/apt/apt.conf.d/10periodic'
        run_command(machine, cmd)


def initialize_default_apt_packages(machine):
    packages = [
        'htop',
    ]
    cmd = 'apt-get install -y {}'.format(' '.join(packages))
    run_command(machine, cmd, silent=True)


def initialize_docker_authentication(machine):
    registry_authenticate(machine)


def initialize_volumes(machine):
    run_command(machine, 'mkdir -p /volumes')
