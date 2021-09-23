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

from msl.io import (
    search,
    copy,
    checksum,
)
from msl.equipment import Config

from . import (
    __version__,
    DEFAULT_WAIT,
)
from .utils import email


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
    def handle_error(message):
        original.close()
        if backup is not None:
            backup.close()
            os.replace(backup_file, corrupt_file)
        logger.error(message)
        if smtp is not None:
            try:
                email(smtp, message, subject='[omega-logger] Database backup issue')
            except Exception as exc:
                logger.error(f'cannot send email: {exc}')

    def safe(minimum=1, maximum=10):
        # Return whether it is safe to continue with the backup.
        # There are 2 cases to consider:
        # 1) the OMEGA iServer is available on the network and values
        #    are being inserted into the database every <wait> seconds
        # 2) it has been a while since the database was modified. This
        #    could be a result of an iServer that is not currently being
        #    used (not plugged in) but a database file exists or the
        #    iServer is not available on the network and reading the
        #    values from it keeps raising a TimeoutError
        dt = time.time() - os.stat(file).st_mtime
        if dt < wait:  # case 1
            return minimum < dt < maximum

        # TODO case 2, not really sure what condition to check
        return dt > 5 * wait

    wait = cfg.value('wait', DEFAULT_WAIT)
    smtp = cfg.find('smtp')
    log_dir = cfg.value('log_dir')
    if cfg.find('backup_dir') is not None:
        backup_dir = cfg.value('backup_dir')
    else:
        backup_dir = os.path.join(log_dir, 'backup')

    os.makedirs(backup_dir, exist_ok=True)

    # where to move a backed-up and corrupt database to
    corrupt_dir = os.path.join(backup_dir, 'corrupt')
    os.makedirs(corrupt_dir, exist_ok=True)

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
    for file in sorted(search(log_dir, pattern=r'\.sqlite3$')):
        basename = os.path.basename(file)
        backup_file = os.path.join(backup_dir, basename)
        corrupt_file = os.path.join(corrupt_dir, basename)
        error_msg = ''
        backup = None
        logger.info(f'processing {basename}')

        # Only start the backup process if it is safe to do so.
        # Don't want to start a backup when there is a chance
        # that a new record will be inserted into the original
        # database during the backup process.
        #
        # Ignore this check when running the tests.
        min_dt, max_dt = 1, 10
        if log_dir != 'tests/resources' and not safe(minimum=min_dt, maximum=max_dt):
            logger.info(f'waiting for the last database modification to be '
                        f'>{min_dt} and <{max_dt} seconds ago')
            while not safe(minimum=min_dt, maximum=max_dt):
                time.sleep(1)

        # make sure that the database is not corrupt
        original = sqlite3.connect(file)
        try:
            check = original.execute('PRAGMA integrity_check;').fetchall()
        except sqlite3.DatabaseError as err:
            check = [(str(err),)]

        if check != [('ok',)]:
            issues = '\n  '.join(item for row in check for item in row)
            handle_error(f'integrity check failed for {basename}\n'
                         f'The database is corrupt:\n  {issues}')
            continue
        logger.info('integrity check passed')

        # create the backup
        backup = sqlite3.connect(backup_file)
        try:
            original.backup(backup)
        except AttributeError:
            # the sqlite3.Connection.backup() method was added in Python 3.7
            copy(file, backup_file, overwrite=True)
            if checksum(file) != checksum(backup_file):
                error_msg = f'backup error for {basename}, checksum mismatch'
        except sqlite3.Error as e:
            error_msg = f'backup error for {basename}\n{e.__class__.__name__}: {e}'

        if error_msg:
            handle_error(error_msg)
            continue
        logger.info('created backup')

        # verify backup
        cursor = backup.execute('SELECT * FROM data;')
        num_missing = 0
        for record in original.execute('SELECT * FROM data;'):
            fetched = cursor.fetchone()
            if fetched is None:
                # although we check above that it is safe to backup the database
                # it is still possible that for very large databases
                # it takes longer than <wait> seconds to perform a backup
                num_missing += 1
                continue
            if record != fetched:
                error_msg = f'verifying backup failed for {basename}\n' \
                            f'record mismatch:' \
                            f'\n  original={record}' \
                            f'\n    backup={fetched}'
                break

        if error_msg:
            handle_error(error_msg)
            continue

        if num_missing > 0:
            # lets see how often this error occurs before we start deciding what should happen
            handle_error(f'verifying backup failed for {basename}, '
                         f'the backed-up database is missing {num_missing} record(s)')
            continue

        if cursor.fetchone() is not None:
            handle_error(f'verifying backup failed for {basename}, '
                         f'the backed-up database contains more records than the original database')
            continue

        backup.close()
        original.close()
        logger.info('verified backup')
        try:
            os.remove(corrupt_file)
        except OSError:
            pass

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
    parser.add_argument(
        '-t', '--test-email',
        action='store_true',
        default=False,
        help='send a test email'
    )
    args = parser.parse_args(args)

    try:
        cfg = Config(os.path.abspath(args.config))
    except OSError as e:
        print(f'{e.__class__.__name__}: {e}', file=sys.stderr)
        return 1

    if args.test_email:
        smtp = cfg.find('smtp')
        if smtp is None:
            print('There is no "smtp" element in the config file. Cannot send email.', file=sys.stderr)
            return 1
        return email(smtp, 'Test', subject='[omega-logger] Test')

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
