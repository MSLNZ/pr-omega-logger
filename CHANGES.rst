=============
Release Notes
=============

Version 0.3.0.dev0
==================
This release is not backward compatible. The structure of the
database table has changed. To upgrade to this version you must
also:

1) Update MSL-Equipment

   ``pip install -U https://github.com/MSLNZ/msl-equipment/archive/main.zip``

2) Update the databases

   i) copy the ``convert_databases.py`` script (located in the root
      directory of the repository) to your computer
   ii) update the value of ``log_dir`` in the script
   iii) run the script

The following features have been made:

- Added

  * a ``Page not found`` template is used for all invalid routes
  * option to disable logging on the WSGI Server by adding a
    ``disable_request_logging`` XML element in the configuration file
  * the ``/connections``, ``/databases``, ``/help`` and ``/reports`` routes
  * support for using a ``Validator`` to check if the data from an OMEGA
    iServer is valid and should be inserted into a database
  * the ``SimpleRange`` and ``WithReset`` validators
  * the ``CalibrationReport.to_json`` method

- Changed

  * the structure of the database table:

    + add a `pid` field (INTEGER PRIMARY KEY)
    + rename the `timestamp` field to be `datetime`
    + the date and time separator is now a **T**
    + remove the microsecond part from the time

  * the separator between a date and time is now always a **T**
  * the `report/temperature` and `report/humidity` XML elements in a configuration
    file support an attribute name of either `unit` or `units`
  * the paths to the register files in a configuration file can be relative paths
    (relative to directory of the configuration file).
  * a ``report_number`` key is now included in the response of the ``/now`` and
    ``/fetch`` routes
  * use a ``ThreadPoolExecutor`` to read the current data from the OMEGA iServers
  * the ``/now`` and ``/fetch`` routes allow for requesting data from multiple
    iServers by using a semi-colon to separate the `serial` or `alias` values
    (e.g., ``/now?serial=1234;56789``)
  * can specify values for both the ``serial`` and ``alias`` parameters in a
    single query for the ``/now`` and ``/fetch`` routes (previously, only the
    ``serial`` value was used if it was specified)


Version 0.2.0 (2021.03.10)
==========================

- Added

  * support for OMEGA iServers with 2 probes
  * a ``Current Readings`` tab
  * the ``/aliases``, ``/now`` and ``/fetch`` routes
  * a custom ``DatetimeRangePicker`` component
  * a custom ``AliasFormatter`` for logging messages for an OMEGA iServer
  * support for the following optional XML elements in a configuration file:
    ``host``, ``port``, ``wait``, ``msg_format``, ``current_readings``,
    ``datetime_range_picker``
  * serial numbers can be separated by whitespace or a comma in the
    configuration file
  * correction coefficients can be separated by a comma or a semi-colon in the
    configuration file
  * use the MSL favicon
  * support for Python 3.8 and 3.9
  * support for Linux

- Changed

  * use ``record.alias`` as the label for each OMEGA iServer in the dropdown menu

- Fixed

  * wait for the register files to be available when starting the
    ``omega-logger`` executable (was an issue for mapped drives during startup)
  * can now download CSV files larger than 2 MB
  * can now specify a single serial number in the configuration file

- Removed

  * support for Python 2.7, 3.4 and 3.5
  * support for macOS

Version 0.1.0 (2018.09.21)
==========================
- Initial release