from subprocess import run, PIPE


def test_no_args():
    process = run(['omega-logger'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr == b'You must pass in the path to the XML configuration file.\n'


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
    assert process.stderr == b"The log_dir value of 'does/not/exist' is not a valid directory.\n"


def test_no_serials():
    process = run(['omega-logger', 'tests/resources/config_no_serials.xml'], stderr=PIPE, stdout=PIPE)
    assert process.returncode == 1
    assert not process.stdout
    assert process.stderr.startswith(b'You have not specified a serial number of an OMEGA iServer.\n')


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
