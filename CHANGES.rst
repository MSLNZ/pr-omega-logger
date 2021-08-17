=============
Release Notes
=============

Version 0.3.0.dev0
==================

- Added

  * the ``/help`` route
  * support for using a ``Validator`` to check if the data from an OMEGA iServer
    is valid and should be inserted into a database
  * the ``SimpleRange`` and ``WithReset`` validators

- Changed

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