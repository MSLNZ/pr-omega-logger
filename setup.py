import re
from setuptools import setup


def read(filename):
    with open(filename) as fp:
        return fp.read()


def fetch_init(key):
    # open the __init__.py file to determine the value instead of importing the package to get the value
    init_text = read(r'omega_logger/__init__.py')
    return re.search(r'{}\s*=\s*(.*)'.format(key), init_text).group(1).strip('\'\"')


setup(
    name='omega_logger',
    version=fetch_init('__version__'),
    author=fetch_init('__author__'),
    author_email='info@measurement.govt.nz',
    url='https://github.com/MSLNZ/pr-omega-logger',
    description='Logs the temperature, humidity and dew point from OMEGA iServer\'s'
                'and creates a Dash webapp to view the data',
    long_description=read('README.rst'),
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=[
        'msl-equipment @ https://github.com/MSLNZ/msl-equipment/archive/master.tar.gz',
        'numpy',
        'gevent',
        'flask',
        'plotly',
        'dash',
        'dash-core-components',
        'dash-html-components',
        'dash-renderer',
    ],
    extras_require={
        'tests': ['pytest', 'requests'],
    },
    packages=['omega_logger'],
    entry_points={
        'console_scripts': [
            'omega-logger = omega_logger.main:start',
        ],
    },
)
