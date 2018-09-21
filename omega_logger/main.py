"""
Start all OMEGA loggers and the web server.

Usage:

omega-logger start /path/to/config.xml
"""
import os
import sys

from msl.equipment import Config


def start():
    if len(sys.argv) == 1:
        sys.exit('You must pass in the path to the XML configuration file.')

    xml = os.path.abspath(sys.argv[1])
    cfg = Config(xml)

    log_dir = cfg.value('log_dir')
    if not log_dir:
        sys.exit('The is no "log_dir" element in the config file.\n'
                 'Where do you want to log the data to?')

    serials = cfg.value('serials')
    if not serials:
        sys.exit('You have not specified any OMEGA serial numbers to log.\n'
                 'Create a "serials" element with each serial number on a new line.')
    serials = [s.strip() for s in serials.splitlines() if s.strip()]

    # change the current working directory to where the package files are located
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # start all OMEGA loggers
    for serial in serials:
        cmd = ' '.join(['start', sys.executable, '-m', 'omega.py', '"{}"'.format(xml), serial])
        os.system(cmd)

    # start the Dash web application
    cmd = ' '.join(['start', sys.executable, '-m', 'webapp.py', '"{}"'.format(xml)])
    os.system(cmd)
