import re
from collections import namedtuple

from .validators import validator_map

__author__ = 'Measurement Standards Laboratory of New Zealand'
__copyright__ = '\xa9 2018 - 2022, ' + __author__
__version__ = '0.4.0'

_v = re.search(r'(\d+)\.(\d+)\.(\d+)[.-]?(.*)', __version__).groups()

version_info = namedtuple('version_info', 'major minor micro releaselevel')(int(_v[0]), int(_v[1]), int(_v[2]), _v[3])
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro, releaselevel) tuple."""

DEFAULT_WAIT = 60
"""The default wait time, in seconds, between OMEGA logging events."""
