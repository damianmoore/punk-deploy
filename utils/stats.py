from utils.ssh import run_command


def get_machine_stats(machine_name):
    stats = {}

    output = run_command(machine_name, 'uptime')
    stats['uptime'] = output.strip().split('up ')[1].split(',')[0]
    stats['load'] = output.strip().split('load average: ')[1]

    output = run_command(machine_name, 'df -h')
    for row in output.split('\n')[1:]:
        cols = row.split()
        if cols[5] == '/':
            stats['disk'] = '{} of {} ({})'.format(cols[2], cols[1], cols[4])
            break

    return stats
