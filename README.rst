Logs the temperature, humidity and dew point from OMEGA iServer's to a database
and creates a Dash_ application. The application is accessed through a web
browser at ``http://<host>:<port>``.

Install
-------
.. code-block:: console

   pip install https://github.com/MSLNZ/pr-omega-logger/archive/master.tar.gz

Usage
-----
.. code-block:: console

   omega-logger /path/to/config.xml

Example config.xml
------------------
This package requires a configuration file that is compatible with `MSL-Equipment`_

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <msl>

        <!-- Optional: Change how the logging information is printed to stdout. -->
        <msg_format>Lab={alias!r} Sn={serial} T={0}&#176;C H={1}% D={2}&#176;C</msg_format>
        <msg_format nprobes="2">{model} T1={0} T2={3} H1={1} H2={4} D1={2} D2={5}</msg_format>

        <!-- Optional: The number of seconds to wait between logging events. -->
        <wait>60</wait>

        <!-- Optional: You can change the host and port values of the web app. -->
        <host>localhost</host>
        <port>8080</port>

        <!-- The directory to save the databases to. -->
        <log_dir>D:\OMEGA</log_dir>

        <!-- The serial numbers (separated by white space and/or a comma) of the iServer's. -->
        <serials>
            4370757
            12481415
        </serials>

        <!--
          The 'coefficients' element represents the polynomial coefficients c0,c1,c2,c3...
          (you can either separate the coefficients by a comma or a semi-colon).
          The corrected value is calculated as "c0 + c1*x + c2*x^2 + c3*x^3 ..."
        -->
        <calibrations>
            <omega serial="4370757">
                <report date="2018-07-21" number="Humidity/2018/386">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.01</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="85">
                        <coefficients>-9.5;0.326;-0.00505;0.0000321</coefficients>
                        <expanded_uncertainty>0.9</expanded_uncertainty>
                    </humidity>
                </report>
                <report date="2016-02-22" number="Humidity/2016/322">
                    <start_date>2016-01-20</start_date>
                    <end_date>2016-01-22</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="17" max="23">
                        <coefficients>0.05</coefficients>
                        <expanded_uncertainty>0.12</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="80">
                        <coefficients>-3.44;0.0487</coefficients>
                        <expanded_uncertainty>0.8</expanded_uncertainty>
                    </humidity>
                </report>
            </omega>
            <omega serial="12481415">
                <!--
                  If an OMEGA iServer uses multiple probes then you can
                  include a 'component' attribute for a 'report' element.
                -->
                <report component="Probe 1" date="2018-07-21" number="Humidity/2018/388">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.04;0.13</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="85">
                        <coefficients>-10.2;0.393;-0.00637;0.000039</coefficients>
                        <expanded_uncertainty>1.0</expanded_uncertainty>
                    </humidity>
                </report>
                <report component="Probe 2" date="2018-07-21" number="Humidity/2018/389">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.1;0.06;0.01</coefficients>
                        <expanded_uncertainty>0.14</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="85">
                        <coefficients>4.2;0.931;0.00482</coefficients>
                        <expanded_uncertainty>0.8</expanded_uncertainty>
                    </humidity>
                </report>
            </omega>
        </calibrations>

        <!-- the location of the equipment records -->
        <registers>
            <register>
                <path>D:\QUAL\EquipmentRegister.xls</path>
                <sheet>Equipment</sheet>
            </register>
        </registers>

        <!-- the location of the connection records -->
        <connections>
            <connection>
                <path>D:\QUAL\EquipmentRegister.xls</path>
                <sheet>OMEGA loggers</sheet>
            </connection>
        </connections>

    </msl>

API
---
Coming soon.

.. _MSL-Equipment: https://msl-equipment.readthedocs.io/en/latest/
.. _Dash: https://plot.ly/products/dash/
