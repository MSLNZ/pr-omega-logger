"""
Start all OMEGA loggers and the web application or perform a database backup.

Usage:

omega-logger /path/to/config.xml
omega-logger /path/to/config.xml --backup
"""
import os
import re
import sys
import time
import logging
import sqlite3
import argparse

from msl.io import search
from msl.equipment import Config

from . import __version__


def run_webapp(cfg):
    """Run the web application and log the data from the iServers.

    Parameters
    ----------
    cfg : :class:`~msl.equipment.config.Config`
        The configuration instance.
    """
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
    def get_absolute_path(p):
        if not os.path.dirname(p) or p.startswith('.'):
            # assume relative to the directory of the configuration file
            return os.path.abspath(os.path.join(os.path.dirname(cfg.path), p))
        return os.path.abspath(p)

    i = 0
    register_path = get_absolute_path(register_path.text)
    connection_path = get_absolute_path(connection_path.text)
    options = ['|', '/', '-', '\\', '|', '/', '-', '\\']
    try:
        while not (os.path.isfile(register_path) and os.path.isfile(connection_path)):
            print('Waiting for the register files to be available ' + options[i], end='\r')
            i += 1
            if i == len(options):
                i = 0
            time.sleep(0.1)
    except KeyboardInterrupt:
        files = '\n'.join(p for p in [register_path, connection_path] if not os.path.isfile(p))
        print(f'KeyboardInterrupt! The following register file(s) are not available\n'
              f'{files}', file=sys.stderr)
        return 1

    if sys.platform == 'win32':
        prefix = 'start '
    elif sys.platform.startswith('linux'):
        prefix = 'gnome-terminal -- '
    else:
        print('OS is not Windows or Linux', file=sys.stderr)
        return 1

    # start logging all OMEGA iServers
    for serial in serials:
        cmd = prefix + ' '.join([sys.executable, '-m', 'omega', f'"{cfg.path}"', serial])
        os.system(cmd)

    # start the Dash web application
    cmd = prefix + ' '.join([sys.executable, '-m', 'webapp', f'"{cfg.path}"', ','.join(serials)])
    os.system(cmd)


def run_backup(cfg):
    """Run the database backup.

    Parameters
    ----------
    cfg : :class:`~msl.equipment.config.Config`
        The configuration instance.
    """
    if sys.version_info[:2] < (3, 7):
        # the sqlite3.Connection.backup() method was added in Python 3.7
        print('Can only perform a database backup with Python 3.7 or later', file=sys.stderr)
        return 1

    if not backup_dir:
        backup_dir = os.path.join(log_dir, 'backup')

    os.makedirs(backup_dir, exist_ok=True)

    # set up logging
    formatter = logging.Formatter('%(asctime)s [%(levelname)-5s] %(message)s')
    formatter.default_msec_format = '%s.%03d'
    file_handler = logging.FileHandler(os.path.join(backup_dir, 'log.txt'))
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)

    logger.info('----- START  BACKUP -----')
    for file in search(log_dir, pattern=r'\.sqlite3$'):
        original = sqlite3.connect(file)
        logger.info(f'processing {os.path.basename(file)}')

        # make sure that the database is not corrupt
        check = original.execute('PRAGMA integrity_check;').fetchall()
        if check != [('ok',)]:
            corrupt = '\n  '.join(item for row in check for item in row)
            logger.error(f'integrity check failed, database is corrupt:\n  {corrupt}')
            original.close()
            continue
        logger.info('integrity check passed')

        # create the backup
        backup = sqlite3.connect(os.path.join(backup_dir, os.path.basename(file)))
        try:
            original.backup(backup)
        except sqlite3.Error as e:
            logger.exception(e)
            continue
        logger.info('created backup')

        # verify backup
        cursor = backup.execute('SELECT * FROM data;')
        for record in original.execute('SELECT * FROM data;'):
            fetched = cursor.fetchone()
            if record != fetched:
                logger.error(
                    f'verifying backup failed, record mismatch:'
                    f'\n  original={record}'
                    f'\n    backup={fetched}'
                )
                backup.close()
                original.close()
                break

        if cursor.fetchone() is None:
            logger.info('verified backup')
        else:
            logger.error('verifying backup failed, database size mismatch')

        backup.close()
        original.close()

    logger.info('----- FINISH BACKUP -----')


def start(*args):
    """Entry point for the console script."""
    if not args:
        args = sys.argv[1:]
        if not args:
            args = ['--help']

    parser = argparse.ArgumentParser(
        description='Start all OMEGA loggers and the web application or perform a database backup.'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='{}'.format(__version__),
        help='show the version number and exit'
    )
    parser.add_argument(
        'config',
        help='the path to a configuration file'
    )
    parser.add_argument(
        '-b', '--backup',
        action='store_true',
        default=False,
        help='perform a database backup'
    )
    args = parser.parse_args(args)

    try:
        cfg = Config(os.path.abspath(args.config))
    except OSError as e:
        print(f'{e.__class__.__name__}: {e}', file=sys.stderr)
        return 1

    log_dir = cfg.value('log_dir')
    if not log_dir:
        print('There is no "log_dir" element in the config file.\n'
              'What directory do you want to log the data to?', file=sys.stderr)
        return 1

    if not os.path.isdir(log_dir):
        print(f'The log_dir value of {log_dir!r} is not a valid directory.', file=sys.stderr)
        return 1

    if args.backup:
        return run_backup(cfg)
    return run_webapp(cfg)
