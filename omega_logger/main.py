"""
Start all OMEGA loggers and the web server.

Usage:

omega-logger /path/to/config.xml
"""
import os
import re
import sys
import time

from msl.equipment import Config


def start():
    if len(sys.argv) == 1:
        print('You must pass in the path to the XML configuration file.', file=sys.stderr)
        return 1

    xml = os.path.abspath(sys.argv[1])
    try:
        cfg = Config(xml)
    except IOError as e:
        print(f'{e.__class__.__name__}: {e}', file=sys.stderr)
        return 1

    log_dir = cfg.value('log_dir')
    if not log_dir:
        print('There is no "log_dir" element in the config file.\n'
              'What directory do you want to log the data to?', file=sys.stderr)
        return 1

    if not os.path.isdir(log_dir):
        print(f'The log_dir value of {log_dir:!r} is not a valid directory.', file=sys.stderr)
        return 1

    serials = cfg.value('serials')
    if not serials:
        print('You have not specified a serial number of an OMEGA iServer.\n'
              'Create a "serials" element with each serial number separated\n'
              'by white space and/or a comma.', file=sys.stderr)
        return 1

    if isinstance(serials, int):  # then only a single serial number was specified
        serials = [str(serials)]
    else:
        serials = [s.strip() for s in re.split(r'\s|,', serials) if s.strip()]

    # change the current working directory to where the package files are located
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    register_path = cfg.find(r'registers/register/path')
    if register_path is None:
        print('You have not specified a "registers/register/path" element '
              'in the configuration file', file=sys.stderr)
        return 1

    connection_path = cfg.find(r'connections/connection/path')
    if connection_path is None:
        print('You have not specified a "connections/connection/path" element '
              'in the configuration file', file=sys.stderr)
        return 1

    # wait for the equipment and connection register files to be available
    # since Windows can take a while to map the Shared drive on startup
    i = 0
    register_path = register_path.text
    connection_path = connection_path.text
    options = ['|', '/', '-', '\\', '|', '/', '-', '\\']
    while not (os.path.isfile(register_path) and os.path.isfile(connection_path)):
        print('Waiting for the register files to be available ' + options[i], end='\r')
        i += 1
        if i == len(options):
            i = 0
        time.sleep(0.1)

    # start all OMEGA loggers
    for serial in serials:
        cmd = ' '.join(['start', sys.executable, '-m', 'omega', f'"{xml}"', serial])
        os.system(cmd)

    # start the Dash web application
    cmd = ' '.join(['start', sys.executable, '-m', 'webapp', f'"{xml}"', ','.join(serials)])
    os.system(cmd)
