import os
import sys
import shutil
from subprocess import run, PIPE

import pytest


def test_no_args():
    process = run(['omega-logger'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 0
    assert process.stdout.startswith(b'usage: omega-logger')
    assert not process.stderr

    process = run(['omega-logger', '--backup'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 2
    assert not process.stdout
    assert b'the following arguments are required: config' in process.stderr


def test_invalid_config_path():
    process = run(['omega-logger', 'cannot/find/config.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b'FileNotFoundError:')


def test_no_log_dir():
    process = run(['omega-logger', 'tests/resources/config_empty.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b'There is no "log_dir" element')


def test_invalid_log_dir():
    process = run(['omega-logger', 'tests/resources/config_invalid_log_dir.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b"The log_dir value of 'does/not/exist' is not a valid directory")


def test_no_serials():
    process = run(['omega-logger', 'tests/resources/config_no_serials.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b'You have not specified a serial number of an OMEGA iServer')


def test_no_registers():
    process = run(['omega-logger', 'tests/resources/config_no_registers.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b'You have not specified a "registers/register/path" element')


def test_no_connections():
    process = run(['omega-logger', 'tests/resources/config_no_connections.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b'You have not specified a "connections/connection/path" element')


@pytest.mark.skipif(sys.version_info[:2] < (3, 7), reason='requires Python 3.7+')
def test_backup_default_dir():
    # the <backup_dir> XML element is not specified in config_backup.xml
    # so the default backup_dir is used
    backup_dir = os.path.join('tests', 'resources', 'backup')
    if os.path.isdir(backup_dir):
        shutil.rmtree(backup_dir)

    process = run(['omega-logger', 'tests/resources/config_backup.xml', '--backup'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 0
    assert not process.stderr
    lines = [line[24:] for line in process.stdout.decode().splitlines()]  # ignore the datetime
    assert lines == [
        '[INFO ] ----- START  BACKUP -----',
        '[INFO ] processing iTHX-W3-5_01234.sqlite3',
        '[INFO ] integrity check passed',
        '[INFO ] created backup',
        '[INFO ] verified backup',
        '[INFO ] processing iTHX-W_56789.sqlite3',
        '[INFO ] integrity check passed',
        '[INFO ] created backup',
        '[INFO ] verified backup',
        '[INFO ] ----- FINISH BACKUP -----'
    ]
    assert os.path.isfile(os.path.join(backup_dir, 'iTHX-W3-5_01234.sqlite3'))
    assert os.path.isfile(os.path.join(backup_dir, 'iTHX-W_56789.sqlite3'))
    assert os.path.isfile(os.path.join(backup_dir, 'log.txt'))
    shutil.rmtree(backup_dir)


@pytest.mark.skipif(sys.version_info[:2] < (3, 7), reason='requires Python 3.7+')
def test_backup_dir():
    # the <backup_dir> XML element is specified in config_backup2.xml
    backup_dir = os.path.join('tests', 'resources', 'temp')
    if os.path.isdir(backup_dir):
        shutil.rmtree(backup_dir)

    process = run(['omega-logger', 'tests/resources/config_backup2.xml', '--backup'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 0
    assert not process.stderr
    lines = [line[24:] for line in process.stdout.decode().splitlines()]  # ignore the datetime
    assert lines == [
        '[INFO ] ----- START  BACKUP -----',
        '[INFO ] processing iTHX-W3-5_01234.sqlite3',
        '[INFO ] integrity check passed',
        '[INFO ] created backup',
        '[INFO ] verified backup',
        '[INFO ] processing iTHX-W_56789.sqlite3',
        '[INFO ] integrity check passed',
        '[INFO ] created backup',
        '[INFO ] verified backup',
        '[INFO ] ----- FINISH BACKUP -----'
    ]
    assert os.path.isfile(os.path.join(backup_dir, 'xxx', 'iTHX-W3-5_01234.sqlite3'))
    assert os.path.isfile(os.path.join(backup_dir, 'xxx', 'iTHX-W_56789.sqlite3'))
    assert os.path.isfile(os.path.join(backup_dir, 'xxx', 'log.txt'))
    shutil.rmtree(backup_dir)


@pytest.mark.skipif(sys.version_info[:2] > (3, 6), reason='not Python 3.6')
def test_backup_py36():
    process = run(['omega-logger', 'tests/resources/config_backup.xml', '--backup'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.rstrip() == b'Can only perform a database backup with Python 3.7 or later'
