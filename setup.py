from setuptools import setup

setup(
    name='omega_logger',
    version='0.2.0.dev0',
    author='Joseph Borbely',
    author_email='joseph.borbely@measurement.govt.nz',
    url='https://github.com/MSLNZ/pr-omega-logger',
    description='Logs the temperature, humidity and dew point from OMEGA iServer\'s'
                'and creates a Dash webapp to view the data',
    long_description=open('README.rst').read().strip(),
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=[
        'msl-equipment @ https://github.com/MSLNZ/msl-equipment/archive/master.tar.gz',
        'gevent',
        'plotly',
        'dash',
        'dash-core-components',
        'dash-html-components',
        'dash-renderer',
    ],
    packages=['omega_logger'],
    entry_points={
        'console_scripts': [
            'omega-logger = omega_logger.main:start',
        ],
    },
)
