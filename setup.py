from setuptools import setup, find_packages

setup(
    name='omega_logger',
    version='0.1.0',
    author='Joseph Borbely',
    author_email='joseph.borbely@measurement.govt.nz',
    url='https://github.com/MSLNZ/omega-logger',
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
    ],
    install_requires=[
        'msl-equipment',
        'gevent',
        'plotly==2.2.3',
        'dash==0.21.1',
        'dash-core-components==0.24.0rc5',
        'dash-html-components==0.11.0',
        'dash-renderer==0.13.0',
    ],
    dependency_links=[
        'https://github.com/MSLNZ/msl-equipment/tarball/master#egg=msl-equipment-0'
    ],
    packages=find_packages(include=('omega_logger',)),
    entry_points={
        'console_scripts': [
            'omega-logger = omega_logger.main:start',
        ],
    },
)
