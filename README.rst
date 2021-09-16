|github tests|

Logs the temperature, humidity and dew point from OMEGA iServers to a database
and creates a Dash_ application. The application is accessed through a web
browser at ``http://<host>:<port>``.

Install
-------
.. code-block:: console

   pip install https://github.com/MSLNZ/pr-omega-logger/archive/main.tar.gz

Usage
-----
To start the web application and to log the data from the iServers, run

.. code-block:: console

   omega-logger /path/to/config.xml

To backup all databases (requires Python 3.7+), run

.. code-block:: console

   omega-logger /path/to/config.xml --backup

Documentation
-------------
The documentation for the endpoints that are available in the web application can be
accessed at ``http://<host>:<port>/help`` once the web application is running.

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

        <!-- Optional: Change the behaviour of the Current Readings tab. -->
        <current_readings>
            <!-- The number of seconds to wait to refresh the page. -->
            <interval>30</interval>
            <!-- The size of the font to use to display the readings. -->
            <font_size>24px</font_size>
            <!-- The amount of whitespace to separate the values by (on the same line). -->
            <margin_right>12px</margin_right>
        </current_readings>

        <!--
          Optional: Settings for the DatetimeRangePicker.
          Each sub-element is also optional.
        -->
        <datetime_range_picker>
            <start>
                <weeks>-1</weeks> <!-- relative to the current date -->
                <days>0</days> <!-- relative to the current date -->
                <hour>7</hour> <!-- absolute value between 0-23 -->
                <minute>0</minute> <!-- absolute value between 0-59 -->
                <second>0</second> <!-- absolute value between 0-59 -->
            </start>
            <end>
                <weeks>0</weeks>
                <days>1</days>
                <hour>12</hour>
                <minute>0</minute>
                <second>0</second>
            </end>
            <min_date>
                <weeks>-52</weeks>
                <days>0</days>
            </min_date>
            <max_date>
                <weeks>0</weeks>
                <days>10</days>
            </max_date>
            <!--
              See https://www.tutorialspoint.com/momentjs/momentjs_format.htm
              for valid date and time formats.
            -->
            <date_format>D MMM YYYY</date_format>
            <time_format>h:mm:ss a</time_format>
            <!--
              See https://www.w3schools.com/jsref/dom_obj_style.asp
              for supported style options.
            -->
            <date_style>
                <color>#514EA6</color>
                <fontSize>32px</fontSize>
            </date_style>
            <time_style>
                <color>#027368</color>
                <fontSize>24px</fontSize>
            </time_style>
            <arrow>
                <width>50px</width>
                <height>70px</height>
                <color>#025159</color>
            </arrow>
            <class_name>datetime-range-left</class_name>
            <text>Refresh</text>
        </datetime_range_picker>

        <!-- Optional: Use a validator to validate the data before inserting it into the database. -->
        <validator hmax="60" dmin="10">simple-range</validator>

        <!-- Optional: Whether to disable logging on the WSGI Server. -->
        <disable_request_logging>true</disable_request_logging>

        <!--
          Optional: The directory to save the database backup to.
          If not specified then uses the "<log_dir>/backup" directory.
        -->
        <backup_dir>D:\OMEGA\backup</backup_dir>

        <!--
          Optional: Settings for sending an email.
          See MSL-IO for more details.
        -->
        <smtp>
          <settings>path/to/smtp_settings</settings>
          <from>me</from>
          <to>person1</to>
          <!-- Can include multiple people to send the email to. --->
          <to>person2</to>
        </smtp>

        <!-- The directory to save the databases to. -->
        <log_dir>D:\OMEGA</log_dir>

        <!-- The serial numbers (separated by white space and/or a comma) of the iServers. -->
        <serials>
            4370757
            12481415
        </serials>

        <calibrations>
            <omega serial="4370757">
                <report date="2018-07-21" number="Humidity/2018/386">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature unit="C" min="18" max="24">
                        <!--
                          The 'coefficients' element represents the polynomial coefficients
                          c0, c1, c2, c3... to apply as the calibration equation. You can
                          either separate the coefficients by a comma or a semi-colon.
                          The calibration equation is
                              x_corrected = x + dx
                          where,
                              dx = c0 + c1*x + c2*x^2 + c3*x^3 + ...
                        -->
                        <coefficients>0.01</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity unit="%rh" min="30" max="85">
                        <coefficients>-9.5;0.326;-0.00505;0.0000321</coefficients>
                        <expanded_uncertainty>0.9</expanded_uncertainty>
                    </humidity>
                </report>
                <report date="2016-02-22" number="Humidity/2016/322">
                    <start_date>2016-01-20</start_date>
                    <end_date>2016-01-22</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature unit="C" min="17" max="23">
                        <coefficients>0.05</coefficients>
                        <expanded_uncertainty>0.12</expanded_uncertainty>
                    </temperature>
                    <humidity unit="%rh" min="30" max="80">
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
                    <temperature unit="C" min="18" max="24">
                        <coefficients>0.04;0.13</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity unit="%rh" min="30" max="85">
                        <coefficients>-10.2;0.393;-0.00637;0.000039</coefficients>
                        <expanded_uncertainty>1.0</expanded_uncertainty>
                    </humidity>
                </report>
                <report component="Probe 2" date="2018-07-21" number="Humidity/2018/389">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature unit="C" min="18" max="24">
                        <coefficients>0.1;0.06;0.01</coefficients>
                        <expanded_uncertainty>0.14</expanded_uncertainty>
                    </temperature>
                    <humidity unit="%rh" min="30" max="85">
                        <coefficients>4.2;0.931;0.00482</coefficients>
                        <expanded_uncertainty>0.8</expanded_uncertainty>
                    </humidity>
                </report>
            </omega>
        </calibrations>

        <!-- The path to the Equipment Records (see MSL-Equipment). -->
        <registers>
            <register>
                <path>D:\QUAL\EquipmentRegister.xls</path>
                <sheet>Equipment</sheet>
            </register>
        </registers>

        <!--
          The path to the Connection Records (see MSL-Equipment).
          A relative path is specified, where "relative" refers to the
          directory where the configuration file is located and not to the
          working directory where the "omega-logger" executable was run.
        -->
        <connections>
            <connection>
                <path>.\omega_connections.xml</path>
            </connection>
        </connections>

    </msl>


.. |github tests| image:: https://github.com/MSLNZ/pr-omega-logger/actions/workflows/run-tests.yml/badge.svg
   :target: https://github.com/MSLNZ/pr-omega-logger/actions/workflows/run-tests.yml

.. _MSL-Equipment: https://msl-equipment.readthedocs.io/en/latest/
.. _Dash: https://plot.ly/products/dash/
