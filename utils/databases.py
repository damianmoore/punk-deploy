import settings
from utils.docker_compose import get_docker_compose_data
from utils.docker_machine import get_machines
from utils.ssh import run_command


def get_databases():
    '''
    Returns the volumes that are mouted in the docker-compose.yml file. Used
    for determining what needs to be synced between machines.
    '''
    databases = set()

    for item, properties in get_docker_compose_data()['services'].items():
        if 'mysql' in properties.get('links', []):
            databases.add(item)

    return sorted(list(databases))


def sync_database_dump(database, src, dst):
    machines = get_machines()
    if src == 'master':
        if dst not in machines:
            raise KeyError('No machine called {}'.format(dst))
        machine = machines[dst]
        run_command('master', 'rsync -avz {} root@{}:/tmp/'.format(settings.MASTER_DATABASE_PATH, machine['ip']), silent=True)
    else:
        raise NotImplementedError()


def load_database_dump(database, dst):
    machines = get_machines()
    if dst not in machines:
        raise KeyError('No machine called {}'.format(dst))
    run_command(dst, 'docker exec mysql bash -c \'MYSQL_PWD=$MYSQL_ROOT_PASSWORD mysql -u root -e "drop database if exists {0}; create database {0}"\''.format(database), silent=True)
    run_command(dst, 'cat /tmp/databases/{0}.sql | docker exec -i mysql bash -c \'MYSQL_PWD=$MYSQL_ROOT_PASSWORD mysql -u root {0}\''.format(database), silent=True)
